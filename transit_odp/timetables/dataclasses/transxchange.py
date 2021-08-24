from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

import pytz
from pydantic import BaseModel, validator

NOC_TAG = "NationalOperatorCode"
LICENCE_NUM_TAG = "LicenceNumber"
OPERATOR_SHORT_NAME_TAG = "OperatorShortName"


class Line(BaseModel):
    line_name: str


class Service(BaseModel):
    service_code: str
    operating_period_start_date: Optional[date]
    operating_period_end_date: Optional[date]
    public_use: bool = True
    lines: List[Line]

    @classmethod
    def from_txc_document(cls, doc):
        lines = [Line(line_name=line) for line in doc.get_all_line_names()]
        service_code = doc.get_service_codes()[0].text
        start_dates = doc.get_operating_period_start_date()
        start_date = start_dates[0].text if len(start_dates) > 0 else None
        end_dates = doc.get_operating_period_end_date()
        end_date = end_dates[0].text if len(end_dates) > 0 else None
        public_uses = doc.get_public_use()
        public_use = public_uses[0].text if len(public_uses) else "true"

        return cls(
            service_code=service_code,
            lines=lines,
            operating_period_start_date=start_date,
            operating_period_end_date=end_date,
            public_use=public_use,
        )


class Operator(BaseModel):
    national_operator_code: str
    operator_short_name: str
    licence_number: str

    @classmethod
    def from_txc_document(cls, doc):
        # Pre-PTI some operators use LicensedOperator, lets see if they have
        # TODO remove get_licensed_operators after PTI hard roll out

        operators = doc.get_operators() + doc.get_licensed_operators()

        if len(operators) < 1:
            return cls(
                national_operator_code="", operator_short_name="", licence_number=""
            )

        operator = operators[0]

        noc = operator.get_text_or_default(NOC_TAG, default="")
        licence_number = operator.get_text_or_default(LICENCE_NUM_TAG, default="")
        operator_short_name = operator.get_text_or_default(
            OPERATOR_SHORT_NAME_TAG, default=""
        )
        return cls(
            national_operator_code=noc,
            operator_short_name=operator_short_name,
            licence_number=licence_number,
        )


class Header(BaseModel):
    revision_number: int
    schema_version: str
    modification: str
    creation_datetime: datetime
    modification_datetime: datetime
    filename: str

    @validator("creation_datetime", "modification_datetime")
    def timezone_validate(cls, dt):
        """
        If datetime does not have a timezone make it UTC.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=pytz.utc)
        return dt

    @classmethod
    def from_txc_document(cls, doc, use_path_filename=False):
        """
        Created a Header object from a TransXChangeDocument.

        Args:
            doc: TransXChangeDocument
            use_path_filename: If True use the actual file name otherwise use
                the attribute in the TXC header.
        """
        path_filename = Path(doc.name).name
        if use_path_filename:
            filename = path_filename
        else:
            filename = doc.get_file_name() or path_filename

        return cls(
            revision_number=doc.get_revision_number(),
            schema_version=doc.get_transxchange_version(),
            modification=doc.get_modification(),
            creation_datetime=doc.get_creation_date_time(),
            modification_datetime=doc.get_modifitication_date_time(),
            filename=filename,
        )


class TXCFile(BaseModel):
    header: Header
    service_code: str
    operator: Optional[Operator]
    service: Service

    @classmethod
    def from_txc_document(cls, doc, use_path_filename=False):
        header = Header.from_txc_document(doc, use_path_filename=use_path_filename)
        service_code = doc.get_service_codes()[0].text
        operator = Operator.from_txc_document(doc)
        service = Service.from_txc_document(doc)
        return cls(
            header=header, service_code=service_code, operator=operator, service=service
        )
