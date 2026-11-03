"""Online, resumable conversion of an integer primary key to bigint.

Follows https://engineering.silverfin.com/pg-zero-downtime-bigint-migration/: a
trigger-mirrored shadow column is backfilled in chunks, proven complete with
VALIDATE CONSTRAINT, indexed concurrently, then swapped in with one short ACCESS
EXCLUSIVE transaction. The phase is derived from the catalog on every run, so a
killed run resumes where it stopped and a finished one is a no-op.

The migration imports this module, so keep its conversion API (PkSpec, Tuning,
convert_pk_to_bigint) backwards compatible.
"""

import os
import random
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Callable, Dict, Mapping, Optional, Tuple, TypeVar

from django.db import IntegrityError, OperationalError, transaction

INT_MAX = 2_147_483_647
PG_NAME_MAX = 63
LOCK_NOT_AVAILABLE = "55P03"
DEADLOCK_DETECTED = "40P01"
CHECK_VIOLATION = "23514"
PROGRESS_EVERY_S = 5.0
# The value the sequence's next nextval() will return.
SEQUENCE_NEXT = (
    "SELECT CASE WHEN is_called THEN last_value + 1 ELSE last_value END FROM {seq}"
)

T = TypeVar("T")


class BigintPkError(Exception):
    pass


class Unsupported(BigintPkError):
    pass


class InconsistentState(BigintPkError):
    pass


class ConcurrentConversion(BigintPkError):
    pass


class LockRetriesExhausted(BigintPkError):
    pass


@dataclass(frozen=True)
class PkSpec:
    table: str
    column: str = "id"


@dataclass(frozen=True)
class Tuning:
    batch_size: int = 50_000
    pause_s: float = 0.0
    # Longest an API insert can queue behind one of our DDL lock requests.
    lock_timeout_ms: int = 1_000
    lock_attempts: int = 60
    lock_backoff_s: Tuple[float, float] = (1.0, 5.0)

    @classmethod
    def from_env(cls, environ: Mapping[str, str] = os.environ) -> "Tuning":
        batch_size = int(environ.get("BIGINT_BACKFILL_BATCH_SIZE", cls.batch_size))
        pause_ms = int(environ.get("BIGINT_BACKFILL_PAUSE_MS", 0))
        if batch_size <= 0 or pause_ms < 0:
            raise ValueError(
                "BIGINT_BACKFILL_BATCH_SIZE must be > 0 and "
                "BIGINT_BACKFILL_PAUSE_MS must be >= 0"
            )
        return cls(batch_size=batch_size, pause_s=pause_ms / 1000)


class IdKind(Enum):
    SERIAL = "serial"
    IDENTITY_BY_DEFAULT = "identity by default"
    IDENTITY_ALWAYS = "identity always"


class Phase(IntEnum):
    ORIGINAL = 0
    SHADOW_INSTALLED = 1
    SHADOW_FILLED = 2
    SHADOW_INDEXED = 3
    CONVERTED = 4


@dataclass(frozen=True)
class Names:
    shadow_col: str
    trigger: str
    check: str
    shadow_index: str

    @classmethod
    def of(cls, spec: PkSpec) -> "Names":
        table, col = spec.table, spec.column
        names = cls(
            shadow_col=f"new_{col}",
            trigger=f"{table}_{col}_bigint_mirror",
            check=f"{table}_new_{col}_mirrors_{col}",
            shadow_index=f"{table}_new_{col}_uniq",
        )
        too_long = [n for n in vars(names).values() if len(n.encode()) > PG_NAME_MAX]
        if too_long:
            raise Unsupported(f"derived names exceed {PG_NAME_MAX} bytes: {too_long}")
        return names


@dataclass(frozen=True)
class Catalog:
    col_type: str
    col_identity: str
    sequence: Optional[str]
    sequence_type: Optional[str]
    pk_constraint: Optional[str]
    pk_columns: Tuple[str, ...]
    inbound_fks: Tuple[str, ...]
    other_indexes_on_col: Tuple[str, ...]
    has_shadow_col: bool
    has_trigger: bool
    check_validated: Optional[bool]
    shadow_index_valid: Optional[bool]

    def kind(self) -> IdKind:
        if self.col_identity == "d":
            return IdKind.IDENTITY_BY_DEFAULT
        if self.col_identity == "a":
            return IdKind.IDENTITY_ALWAYS
        if self.sequence:
            return IdKind.SERIAL
        raise Unsupported("primary key is not backed by a sequence")

    def phase(self) -> Phase:
        shadow = (
            self.has_shadow_col,
            self.has_trigger,
            self.check_validated is not None,
            self.shadow_index_valid is not None,
        )
        if self.col_type not in ("integer", "bigint"):
            raise Unsupported(f"column type {self.col_type} is not integer or bigint")
        if not any(shadow):
            if self.col_type == "integer":
                return Phase.ORIGINAL
            return Phase.CONVERTED
        if self.col_type == "integer" and all(shadow[:3]):
            if not self.check_validated and self.shadow_index_valid is None:
                return Phase.SHADOW_INSTALLED
            if self.check_validated and self.shadow_index_valid:
                return Phase.SHADOW_INDEXED
            if self.check_validated:
                return Phase.SHADOW_FILLED
        raise InconsistentState(f"catalog matches no conversion phase: {self}")


def read_catalog(cursor, spec: PkSpec, names: Names) -> Catalog:
    cursor.execute("SELECT to_regclass(%s)::oid", [_q(spec.table)])
    (table_oid,) = cursor.fetchone()
    if table_oid is None:
        raise Unsupported(f"table {spec.table} does not exist")

    def scalar(sql, params):
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return row[0] if row else None

    def strings(sql, params):
        cursor.execute(sql, params)
        return tuple(row[0] for row in cursor.fetchall())

    cursor.execute(
        """
        SELECT format_type(atttypid, atttypmod), attidentity
        FROM pg_attribute
        WHERE attrelid = %s AND attname = %s AND NOT attisdropped
        """,
        [table_oid, spec.column],
    )
    row = cursor.fetchone()
    if row is None:
        raise Unsupported(f"column {spec.table}.{spec.column} does not exist")
    col_type, col_identity = row
    sequence = scalar(
        "SELECT pg_get_serial_sequence(%s, %s)", [_q(spec.table), spec.column]
    )
    sequence_type = None
    if sequence:
        sequence_type = scalar(
            "SELECT format_type(seqtypid, NULL) FROM pg_sequence "
            "WHERE seqrelid = %s::regclass",
            [sequence],
        )
    cursor.execute(
        """
        SELECT c.conname, c.conindid,
               array(SELECT a.attname
                     FROM unnest(c.conkey) WITH ORDINALITY k(attnum, n)
                     JOIN pg_attribute a ON a.attrelid = c.conrelid
                                        AND a.attnum = k.attnum
                     ORDER BY k.n)
        FROM pg_constraint c
        WHERE c.conrelid = %s AND c.contype = 'p'
        """,
        [table_oid],
    )
    pk_constraint, pk_index, pk_columns = cursor.fetchone() or (None, None, [])
    return Catalog(
        col_type=col_type,
        col_identity=col_identity,
        sequence=sequence,
        sequence_type=sequence_type,
        pk_constraint=pk_constraint,
        pk_columns=tuple(pk_columns),
        inbound_fks=strings(
            "SELECT conname FROM pg_constraint WHERE confrelid = %s AND contype = 'f'",
            [table_oid],
        ),
        other_indexes_on_col=strings(
            """
            SELECT i.indexrelid::regclass::text
            FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attname = %s
            WHERE i.indrelid = %s
              AND i.indexrelid IS DISTINCT FROM %s
              AND a.attnum = ANY (i.indkey)
            """,
            [spec.column, table_oid, pk_index],
        ),
        has_shadow_col=bool(
            scalar(
                "SELECT 1 FROM pg_attribute "
                "WHERE attrelid = %s AND attname = %s AND NOT attisdropped",
                [table_oid, names.shadow_col],
            )
        ),
        has_trigger=bool(
            scalar(
                "SELECT 1 FROM pg_trigger WHERE tgrelid = %s AND tgname = %s",
                [table_oid, names.trigger],
            )
        ),
        check_validated=scalar(
            "SELECT convalidated FROM pg_constraint "
            "WHERE conrelid = %s AND conname = %s",
            [table_oid, names.check],
        ),
        shadow_index_valid=scalar(
            """
            SELECT i.indisvalid
            FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
            WHERE i.indrelid = %s AND c.relname = %s
            """,
            [table_oid, names.shadow_index],
        ),
    )


@dataclass
class ConversionReport:
    table: str
    column: str
    kind: IdKind
    step_seconds: Dict[str, float] = field(default_factory=dict)
    rows_backfilled: int = 0
    lock_attempts: Dict[str, int] = field(default_factory=dict)
    next_id: Optional[int] = None
    total_seconds: float = 0.0

    def summary_line(self) -> str:
        backfill_s = self.step_seconds.get("backfill", 0.0)
        rate = self.rows_backfilled / backfill_s if backfill_s else 0.0
        parts = [
            "SUMMARY",
            f"table={self.table}.{self.column}",
            f"kind={self.kind.value.replace(' ', '_')}",
            "phase=CONVERTED",
            f"total={self.total_seconds:.2f}s",
            *(f"{name}={s:.2f}s" for name, s in self.step_seconds.items()),
            f"rows={self.rows_backfilled}",
            f"rate={rate:.0f}/s",
            f"next_id={self.next_id}",
            "lock_attempts="
            + (",".join(f"{k}:{v}" for k, v in self.lock_attempts.items()) or "-"),
        ]
        return " ".join(parts)


@dataclass
class _Run:
    connection: object
    spec: PkSpec
    names: Names
    tuning: Tuning
    out: Callable[[str], None]
    report: ConversionReport

    def catalog(self) -> Catalog:
        with self.connection.cursor() as c:
            return read_catalog(c, self.spec, self.names)

    def execute(self, template: str, params=None, **parts):
        """Run `template`, filling {table} {col} {shadow} {trigger} {check}
        {index} with this run's quoted identifiers, and any extra `parts`."""
        names = self.names
        identifiers = {
            "table": self.spec.table,
            "col": self.spec.column,
            "shadow": names.shadow_col,
            "trigger": names.trigger,
            "check": names.check,
            "index": names.shadow_index,
        }
        query = template.format(
            **{key: _q(value) for key, value in identifiers.items()}, **parts
        )
        with self.connection.cursor() as c:
            c.execute(query, params)
            return c.fetchall() if c.description else c.rowcount


@dataclass(frozen=True)
class Step:
    name: str
    reaches: Phase
    apply: Callable[[_Run], None]


def _print(line: str) -> None:
    print(line, flush=True)


def convert_pk_to_bigint(
    connection,
    spec: PkSpec,
    tuning: Tuning = Tuning(),
    out: Callable[[str], None] = _print,
) -> ConversionReport:
    """Drive `spec` from whatever phase it is in to CONVERTED.

    Needs an autocommit connection (a non-atomic migration or a shell) because
    it runs CREATE INDEX CONCURRENTLY and commits each backfill chunk.
    """
    if connection.in_atomic_block or not connection.get_autocommit():
        raise Unsupported("convert_pk_to_bigint must run outside a transaction")
    names = Names.of(spec)
    prefixed = _prefixed(spec, out)
    started = time.monotonic()
    with _exclusive_session(connection, spec):
        with connection.cursor() as c:
            cat = read_catalog(c, spec, names)
            phase = cat.phase()
            if phase == Phase.ORIGINAL:
                _check_preconditions(spec, cat)
            prefixed(_describe(c, spec, cat, phase))
        run = _Run(
            connection,
            spec,
            names,
            tuning,
            prefixed,
            ConversionReport(spec.table, spec.column, cat.kind()),
        )
        for step in STEPS:
            if run.catalog().phase() >= step.reaches:
                continue
            step_started = time.monotonic()
            step.apply(run)
            elapsed = time.monotonic() - step_started
            run.report.step_seconds[step.name] = elapsed
            attempts = run.report.lock_attempts.get(step.name)
            prefixed(
                f"{step.name}: done in {elapsed:.2f}s"
                + (f" (lock attempts={attempts})" if attempts else "")
            )
            if run.catalog().phase() < step.reaches:
                raise InconsistentState(f"{step.name} did not reach {step.reaches!r}")
        run.report.next_id = _check_converted(run)
        if run.report.step_seconds:
            run.execute("ANALYZE {table}")
    run.report.total_seconds = time.monotonic() - started
    prefixed(run.report.summary_line())
    return run.report


def _prefixed(spec: PkSpec, out: Callable[[str], None]) -> Callable[[str], None]:
    return lambda line: out(f"[bigint {spec.table}.{spec.column}] {line}")


@contextmanager
def _exclusive_session(connection, spec: PkSpec):
    """Advisory lock so two runners can't interleave, and no statement timeout
    because the backfill, VALIDATE and CIC legitimately run for minutes."""
    key = f"bigint_pk:{spec.table}"
    with connection.cursor() as c:
        c.execute("SELECT pg_try_advisory_lock(hashtext(%s))", [key])
        if not c.fetchone()[0]:
            raise ConcurrentConversion(f"{key} is held by another session")
        c.execute("SET statement_timeout = 0")
    try:
        yield
    finally:
        with connection.cursor() as c:
            c.execute("RESET statement_timeout")
            c.execute("SELECT pg_advisory_unlock(hashtext(%s))", [key])


def _check_preconditions(spec: PkSpec, cat: Catalog) -> None:
    cat.kind()
    if cat.pk_columns != (spec.column,):
        raise Unsupported(f"primary key is {cat.pk_columns}, expected ({spec.column},)")
    if cat.inbound_fks:
        raise Unsupported(
            f"foreign keys reference {spec.table}: {', '.join(cat.inbound_fks)}"
        )
    # The swap drops the old column, which would silently drop these indexes.
    if cat.other_indexes_on_col:
        raise Unsupported(
            f"indexes other than the primary key use {spec.column}: "
            f"{', '.join(cat.other_indexes_on_col)}"
        )


def _describe(cursor, spec: PkSpec, cat: Catalog, phase: Phase) -> str:
    cursor.execute(
        "SELECT min({col}), max({col}) FROM {table}".format(
            table=_q(spec.table), col=_q(spec.column)
        )
    )
    min_id, max_id = cursor.fetchone()
    cursor.execute(
        "SELECT greatest(reltuples, 0)::bigint, pg_size_pretty(pg_table_size(oid)) "
        "FROM pg_class WHERE oid = to_regclass(%s)",
        [_q(spec.table)],
    )
    est_rows, size = cursor.fetchone()
    next_id = None
    if cat.sequence:
        cursor.execute(SEQUENCE_NEXT.format(seq=cat.sequence))
        (next_id,) = cursor.fetchone()
    utilisation = f"{100 * (next_id - 1) / INT_MAX:.2f}%" if next_id else "-"
    return (
        f"kind={cat.kind().value.replace(' ', '_')} column={cat.col_type} "
        f"sequence={cat.sequence}({cat.sequence_type}) next_id={next_id} "
        f"int_utilisation={utilisation} min_id={min_id} max_id={max_id} "
        f"est_rows={est_rows} size={size} phase={phase.name}"
    )


def _check_converted(run: _Run) -> int:
    cat = run.catalog()
    ((max_id,),) = run.execute("SELECT max({col}) FROM {table}")
    next_id = None
    if cat.sequence:
        ((next_id,),) = run.execute(SEQUENCE_NEXT, seq=cat.sequence)
    if cat.sequence_type != "bigint" or next_id is None or next_id <= (max_id or 0):
        raise InconsistentState(
            f"converted column has sequence {cat.sequence}({cat.sequence_type}) "
            f"at {next_id} with max id {max_id}"
        )
    return next_id


def _sqlstate(error: Exception) -> Optional[str]:
    return getattr(error.__cause__, "pgcode", None)


def _with_retry(run: _Run, label: str, sqlstates, attempt_fn: Callable[[], T]) -> T:
    """Retry `attempt_fn` (all-or-nothing) on the given SQLSTATEs with jittered
    backoff. Many short lock waits keep API inserts from queueing behind us for
    long, unlike one long wait behind a slow report query."""
    for attempt in range(1, run.tuning.lock_attempts + 1):
        try:
            result = attempt_fn()
        except OperationalError as error:
            if _sqlstate(error) not in sqlstates:
                raise
            run.out(
                f"{label}: {_sqlstate(error)} on attempt "
                f"{attempt}/{run.tuning.lock_attempts}, retrying"
            )
            time.sleep(random.uniform(*run.tuning.lock_backoff_s))
        else:
            attempts = run.report.lock_attempts
            attempts[label] = max(attempts.get(label, 0), attempt)
            return result
    raise LockRetriesExhausted(
        f"{label}: gave up after {run.tuning.lock_attempts} attempts"
    )


def _locked(run: _Run, label: str, body: Callable[[], None]) -> None:
    """Run `body` in one transaction holding ACCESS EXCLUSIVE on the table."""

    def attempt():
        with transaction.atomic(using=run.connection.alias):
            run.execute(
                "SET LOCAL lock_timeout = %s", [f"{run.tuning.lock_timeout_ms}ms"]
            )
            # Strongest lock first: one queue wait and no lock-upgrade deadlocks.
            run.execute("LOCK TABLE {table} IN ACCESS EXCLUSIVE MODE")
            body()

    _with_retry(run, label, {LOCK_NOT_AVAILABLE}, attempt)


INSTALL_SHADOW = """
    ALTER TABLE {table} ADD COLUMN {shadow} bigint NOT NULL DEFAULT 0;

    CREATE OR REPLACE FUNCTION {trigger}() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        NEW.{shadow} := NEW.{col};
        RETURN NEW;
    END $$;

    -- UPDATE too: an update of a not-yet-backfilled row must pass the CHECK.
    CREATE TRIGGER {trigger} BEFORE INSERT OR UPDATE ON {table}
        FOR EACH ROW EXECUTE FUNCTION {trigger}();

    ALTER TABLE {table} ADD CONSTRAINT {check} CHECK ({shadow} = {col}) NOT VALID;
"""


def _install_shadow(run: _Run) -> None:
    _locked(run, "install_shadow", lambda: run.execute(INSTALL_SHADOW))


def _backfill(run: _Run) -> None:
    """Mirror old rows into the shadow column, then let VALIDATE CONSTRAINT prove
    every row is mirrored rather than trusting the loop bounds."""
    bounds = "SELECT min({col}), max({col}) FROM {table}"
    validate = "ALTER TABLE {table} VALIDATE CONSTRAINT {check}"
    ((low, high),) = run.execute(bounds)
    if low is not None:
        _sweep(run, low, _resume_point(run, low, high + 1))
    try:
        run.execute(validate)
    except IntegrityError as error:
        if _sqlstate(error) != CHECK_VIOLATION:
            raise
        run.out("backfill: VALIDATE found unmirrored rows, sweeping the whole table")
        ((low, high),) = run.execute(bounds)
        _sweep(run, low, high + 1)
        run.execute(validate)


def _resume_point(run: _Run, low: int, high: int) -> int:
    """Smallest id at and above which every row is mirrored.

    The backfill runs downwards and the trigger mirrors new rows at the top, so
    mirrored rows form a suffix of the id range and can be binary searched. If a
    stray update breaks that, VALIDATE fails and the full sweep covers it.
    """
    while low < high:
        mid = (low + high) // 2
        rows = run.execute(
            """
            SELECT {shadow} = {col} FROM {table}
            WHERE {col} >= %s
            ORDER BY {col} LIMIT 1
            """,
            [mid],
        )
        if not rows or rows[0][0]:
            high = mid
        else:
            low = mid + 1
    return high


def _sweep(run: _Run, low: int, high: int) -> None:
    total = max(high - low, 1)
    started = last_report = time.monotonic()
    upper = high
    while upper > low:
        # Chunk by row count, not id span, so gaps in the ids cost nothing.
        boundary = run.execute(
            """
            SELECT {col} FROM {table}
            WHERE {col} >= %s AND {col} < %s
            ORDER BY {col} DESC OFFSET %s LIMIT 1
            """,
            [low, upper, run.tuning.batch_size - 1],
        )
        lower = boundary[0][0] if boundary else low
        run.report.rows_backfilled += _backfill_chunk(run, lower, upper)
        upper = lower
        now = time.monotonic()
        if now - last_report >= PROGRESS_EVERY_S:
            last_report = now
            done = high - upper
            rate = run.report.rows_backfilled / (now - started)
            eta = (upper - low) / (done / (now - started))
            run.out(
                f"backfill: {run.report.rows_backfilled} rows, "
                f"{100 * done / total:.1f}% of id range, {rate:.0f} rows/s, "
                f"eta {eta:.0f}s"
            )
        if run.tuning.pause_s:
            time.sleep(run.tuning.pause_s)


def _backfill_chunk(run: _Run, lower: int, upper: int) -> int:
    return _with_retry(
        run,
        "backfill",
        {DEADLOCK_DETECTED, LOCK_NOT_AVAILABLE},
        lambda: run.execute(
            """
            UPDATE {table} SET {shadow} = {col}
            WHERE {col} >= %s AND {col} < %s AND {shadow} <> {col}
            """,
            [lower, upper],
        ),
    )


def _build_unique_index(run: _Run) -> None:
    # An interrupted CREATE INDEX CONCURRENTLY leaves an INVALID index behind.
    run.execute("DROP INDEX CONCURRENTLY IF EXISTS {index}")
    run.execute("CREATE UNIQUE INDEX CONCURRENTLY {index} ON {table} ({shadow})")


DROP_MIRROR = """
    DROP TRIGGER {trigger} ON {table};
    DROP FUNCTION {trigger}();
    ALTER TABLE {table} DROP CONSTRAINT {check};
    ALTER TABLE {table} DROP CONSTRAINT {pk};
"""

SWAP_SERIAL_COLUMN = """
    ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT;
    -- Otherwise dropping the old column drops the sequence with it.
    ALTER SEQUENCE {seq} OWNED BY NONE;
    ALTER TABLE {table} DROP COLUMN {col};
    ALTER TABLE {table} RENAME COLUMN {shadow} TO {col};
    -- PG raises MAXVALUE to the bigint limit when it was at the int limit.
    ALTER SEQUENCE {seq} AS bigint OWNED BY {table}.{col};
    ALTER TABLE {table} ALTER COLUMN {col} SET DEFAULT nextval({seq_name}::regclass);
    SELECT setval({seq_name}, {next_id}, false);
"""

# An identity sequence can't change owner, so it goes with the old column and
# the new column gets a fresh bigint one under the same name.
SWAP_IDENTITY_COLUMN = """
    ALTER TABLE {table} DROP COLUMN {col};
    ALTER TABLE {table} RENAME COLUMN {shadow} TO {col};
    ALTER TABLE {table} ALTER COLUMN {col} DROP DEFAULT;
    ALTER TABLE {table} ALTER COLUMN {col} ADD GENERATED {generated} AS IDENTITY
        (SEQUENCE NAME {seq} START WITH {next_id});
"""

ATTACH_PK = "ALTER TABLE {table} ADD CONSTRAINT {pk} PRIMARY KEY USING INDEX {index}"


def _swap(run: _Run) -> None:
    def body():
        cat = run.catalog()
        if cat.phase() != Phase.SHADOW_INDEXED:
            raise InconsistentState(
                f"swap expected SHADOW_INDEXED, got {cat.phase()!r}"
            )
        ((sequence_next,),) = run.execute(SEQUENCE_NEXT, seq=cat.sequence)
        ((max_id,),) = run.execute("SELECT max({shadow}) FROM {table}")
        kind = cat.kind()
        swap_column = (
            SWAP_SERIAL_COLUMN if kind is IdKind.SERIAL else SWAP_IDENTITY_COLUMN
        )
        pk = _q(cat.pk_constraint)
        run.execute(DROP_MIRROR, pk=pk)
        run.execute(
            swap_column,
            seq=cat.sequence,
            seq_name=_literal(cat.sequence),
            next_id=int(max(sequence_next, (max_id or 0) + 1)),
            generated="ALWAYS" if kind is IdKind.IDENTITY_ALWAYS else "BY DEFAULT",
        )
        run.execute(ATTACH_PK, pk=pk)

    _locked(run, "swap", body)


STEPS: Tuple[Step, ...] = (
    Step("install_shadow", Phase.SHADOW_INSTALLED, _install_shadow),
    Step("backfill", Phase.SHADOW_FILLED, _backfill),
    Step("build_unique_index", Phase.SHADOW_INDEXED, _build_unique_index),
    Step("swap", Phase.CONVERTED, _swap),
)


def _q(name: str) -> str:
    """Quote an identifier as text, for catalog functions that take a name."""
    return '"' + name.replace('"', '""') + '"'


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
