import re

from transit_odp.validate.xml import XMLSyntaxError

INVALID_VALUE_PATTERN = "is not a valid value of the atomic type"
INVALID_ROOT_PATTERN = (
    "No matching global declaration available for the validation root."
)
UNEXPECTED_ELEMENT_PATTERN = "This element is not expected."
MISSING_ELEMENT_PATTERN = "This element is not expected. Expected is "
MISMATCHED_TAG_PATTERN = "mismatched tag"

HEADER = "The dataset contains an XML file which couldn't be parsed </br> - "


class XMLErrorMessageRenderer:
    def _get_invalid_value_message(self):
        """Renders messages of a type 'FromDate': '2020-01-01T00:00' is not a valid
        value of the atomic type 'xs:dateTime'."""
        pattern = r"'(\{\S*\})*(.*)': (.*)"
        matches = re.findall(pattern, self._message)
        if matches:
            _, element, description = matches[0]

        return HEADER + "Invalid values"

    def _get_unexpected_element_message(self):
        return HEADER + "Invalid elements"

    def _get_invalid_root_element_message(self):
        return HEADER + "Invalid elements"

    def _get_mismatched_tag_message(self):
        return HEADER + "Mismatched tag"

    def _get_missing_element_message(self):
        return HEADER + "Elements not defined"

    def _get_none(self):
        return None

    def _get_titled_error(self):
        return self._message.title()

    def _get_generic_error(self):
        return "This dataset contains XML that doesn't conform to the schema."

    def get_message(self):
        return self.renderer()

    def __init__(self, message: str, error_code: str = None):
        self._message = message
        self._error_code = error_code
        if INVALID_VALUE_PATTERN in message:
            self.renderer = self._get_invalid_value_message
        elif MISSING_ELEMENT_PATTERN in message:
            self.renderer = self._get_missing_element_message
        elif UNEXPECTED_ELEMENT_PATTERN in message:
            self.renderer = self._get_unexpected_element_message
        elif INVALID_ROOT_PATTERN in message:
            self.renderer = self._get_invalid_root_element_message
        elif MISMATCHED_TAG_PATTERN in message:
            self.renderer = self._get_mismatched_tag_message
        else:
            if self._error_code == XMLSyntaxError.code:
                self.renderer = self._get_generic_error
            else:
                self.renderer = self._get_titled_error
