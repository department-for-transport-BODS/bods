from datetime import datetime
from pathlib import Path
from typing import Optional

import pytz
from pydantic import BaseModel, validator

NOC_TAG = "NationalOperatorCode"
LICENCE_NUM_TAG = "LicenceNumber"
OPERATOR_SHORT_NAME_TAG = "OperatorShortName"


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
    modificaton_datetime: datetime
    filename: str

    @validator("creation_datetime", "modificaton_datetime")
    def timezone_validate(cls, dt):
        """
        If datetime does not have a timezone make it UTC.
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=pytz.utc)
        return dt

    @classmethod
    def from_txc_document(cls, doc):
        filename = doc.get_file_name() or Path(doc.name).name
        return cls(
            revision_number=doc.get_revision_number(),
            schema_version=doc.get_transxchange_version(),
            modification=doc.get_modification(),
            creation_datetime=doc.get_creation_date_time(),
            modificaton_datetime=doc.get_modifitication_date_time(),
            filename=filename,
        )


class TXCFile(BaseModel):
    header: Header
    service_code: str
    operator: Optional[Operator]

    @classmethod
    def from_txc_document(cls, doc):
        header = Header.from_txc_document(doc)
        service_code = doc.get_service_codes()[0].text
        operator = Operator.from_txc_document(doc)
        return cls(header=header, service_code=service_code, operator=operator)
