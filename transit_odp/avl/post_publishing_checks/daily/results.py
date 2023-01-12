import logging
from typing import Optional

from transit_odp.avl.post_publishing_checks.constants import (
    SIRIVM_TO_TXC_MAP,
    ErrorCategory,
    MiscFieldPPC,
    SirivmField,
)

logger = logging.getLogger(__name__)

# For debug (temporary)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class FieldValidation:
    def __init__(self, sirivm_field: SirivmField, txc_name: Optional[str] = None):
        self.sirivm_field = sirivm_field
        self.sirivm_value = None
        self.txc_name = txc_name
        self.txc_value = None
        self.matches = False


class ValidationResult:
    def __init__(self):
        self.validated = []
        for field in SirivmField:
            self.validated.append(FieldValidation(field, SIRIVM_TO_TXC_MAP.get(field)))
        self.misc = {field: None for field in MiscFieldPPC}
        self.errors = {category: [] for category in ErrorCategory}
        self.journey_matched = False
        self.stats = None

    def set_sirivm_value(self, sirivm_field: SirivmField, value: str):
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                validated_field.sirivm_value = value
                return
        assert False

    def set_txc_value(self, sirivm_field: SirivmField, value: str):
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                validated_field.txc_value = value
                return
        assert False

    def set_matches(self, sirivm_field: SirivmField):
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                validated_field.matches = True
                return
        assert False

    def add_error(self, category: ErrorCategory, error: str):
        self.errors[category].append(error)
        logger.info(error)

    def sirivm_value(self, sirivm_field: SirivmField) -> Optional[str]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.sirivm_value
        assert False

    def txc_value(self, sirivm_field: SirivmField) -> Optional[str]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.txc_value
        assert False

    def matches(self, sirivm_field: SirivmField) -> Optional[bool]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.matches
        assert False

    def set_misc_value(self, misc_field: MiscFieldPPC, value: str):
        self.misc[misc_field] = value

    def misc_value(self, misc_field: MiscFieldPPC) -> str:
        return self.misc[misc_field]

    def set_journey_matched(self):
        self.journey_matched = True

    def journey_was_matched(self) -> bool:
        return self.journey_matched
