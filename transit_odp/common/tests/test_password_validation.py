import unittest
from django.core.exceptions import ValidationError

from transit_odp.common.password_validation import CustomPasswordValidator


class CustomPasswordValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = CustomPasswordValidator()

    def test_valid_password(self):
        # Valid password should not raise any ValidationError
        try:
            self.validator.validate("ValidPassword123!")
        except ValidationError as e:
            self.fail(f"Validation error raised unexpectedly: {e}")

    def test_password_no_upper_or_lower(self):
        # Password lacks both uppercase and lowercase characters
        with self.assertRaises(ValidationError):
            self.validator.validate("nocase123!")

    def test_password_no_digit(self):
        # Password lacks any digit
        with self.assertRaises(ValidationError):
            self.validator.validate("NoDigitHere!")

    def test_password_no_special_character(self):
        # Password lacks any special character
        with self.assertRaises(ValidationError):
            self.validator.validate("NoSpecial123")
