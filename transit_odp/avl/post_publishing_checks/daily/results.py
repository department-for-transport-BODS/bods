import logging
from typing import Optional

from transit_odp.avl.post_publishing_checks.constants import (
    SIRIVM_TO_TXC_MAP,
    ErrorCategory,
    MiscFieldPPC,
    SirivmField,
    TransXChangeField,
    ErrorCode,
)


logger = logging.getLogger(__name__)

# For debug (temporary)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class FieldValidation:
    def __init__(self, sirivm_field: SirivmField, txc_name: Optional[str] = None):
        self.sirivm_field = sirivm_field
        self.sirivm_value = None
        self.sirivm_line_num = None
        self.txc_name = txc_name
        self.txc_value = None
        self.txc_line_num = None
        self.matches = False


class ValidationResult:
    def __init__(self):
        self.validated = []
        for field in SirivmField:
            self.validated.append(FieldValidation(field, SIRIVM_TO_TXC_MAP.get(field)))
        self.misc = {field: None for field in MiscFieldPPC}
        self.errors = {category: [] for category in ErrorCategory}
        self.errors_code = {error_code.name: False for error_code in ErrorCode}
        self.transxchange_field = {field: None for field in TransXChangeField}
        self.journey_matched = False
        self.stats = None

    def set_sirivm_value(
        self, sirivm_field: SirivmField, value: str, line_num: int = None
    ):
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                validated_field.sirivm_value = value
                validated_field.sirivm_line_num = line_num
                return
        assert False

    def set_txc_value(
        self, sirivm_field: SirivmField, value: str, line_num: int = None
    ):
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                validated_field.txc_value = value
                validated_field.txc_line_num = line_num
                return
        assert False

    def set_matches(self, sirivm_field: SirivmField):
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                validated_field.matches = True
                return
        assert False

    def add_error(
        self, category: ErrorCategory, error: str, error_code: ErrorCode = None
    ):
        """
        Adds an error message to the specified category and logs the error.

        Args:
            category (ErrorCategory): The category to which the error belongs.
            error (str): The error message to be added.
            error_code (ErrorCode, optional): The error code associated with the error. Defaults to None.
        """
        self.errors[category].append(error)
        if error_code:
            self.errors_code[error_code.name] = True
        logger.info(error)

    def sirivm_value(self, sirivm_field: SirivmField) -> Optional[str]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.sirivm_value
        assert False

    def sirivm_line_number(self, sirivm_field: SirivmField) -> Optional[int]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.sirivm_line_num
        assert False

    def txc_value(self, sirivm_field: SirivmField) -> Optional[str]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.txc_value
        assert False

    def txc_line_number(self, sirivm_field: SirivmField) -> Optional[int]:
        for validated_field in self.validated:
            if validated_field.sirivm_field == sirivm_field:
                return validated_field.txc_line_num
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

    def set_transxchange_attribute(self, trans_field: TransXChangeField, value: str):
        """
        Sets the value of a specified TransXChange field.

        Args:
            trans_field (TransXChangeField): The field for which the value is to be set.
            value (str): The value to be set for the specified field.
        """
        self.transxchange_field[trans_field] = value

    def transxchange_attribute(self, trans_field: TransXChangeField) -> Optional[str]:
        """
        Retrieves the value of a specified TransXChange field.

        Args:
            trans_field (TransXChangeField): The field for which the value is to be retrieved.

        Returns:
            Optional[str]: The value of the specified field, if it exists. Otherwise, None.
        """
        return self.transxchange_field.get(trans_field, None)
