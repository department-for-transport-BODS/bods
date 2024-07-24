import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext


class CustomPasswordValidator:
    """
    Custom password validator for Django authentication system.

    This validator checks if a password meets the following criteria:
    - Contains at least one uppercase letter.
    - Contains at least one lowercase letter.
    - Contains at least one digit.
    - Contains at least one special character from the set: ~!@#$%^&*()_+{}":;'<>\?/|

    """

    def validate(self, password, user=None):
        """
        Validate the password against the defined criteria.

        Args:
        - password (str): The password to validate.
        - user (object, optional): The user object (default: None).

        Raises:
        - ValidationError: If the password does not meet any of the validation criteria.
        """
        # Track failed criteria
        errors = []

        # Check if password contains both uppercase and lowercase characters
        if not any(char.isupper() for char in password) or not any(
            char.islower() for char in password
        ):
            errors.append(
                gettext(
                    "Password must contain both uppercase and lowercase characters."
                )
            )

        # Check if password contains at least one digit
        if not any(char.isdigit() for char in password):
            errors.append(gettext("Password must contain at least one digit (0-9)."))

        # Check if password contains at least one special character
        special_characters = r'[~\!@#\$%\^&\*\(\)_\+{}":;\'<>\?/\|]'
        if not re.search(special_characters, password):
            errors.append(
                gettext(
                    "Password must contain at least one special character (e.g., !@#$%^&*)."
                )
            )

        # Raise a single ValidationError if any checks failed
        if errors:
            raise ValidationError(
                "\n".join(errors),
                code="password_invalid",
            )

    def get_help_text(self):
        """
        Get help text describing the password requirements.

        Returns:
        - str: Help text describing the password requirements.
        """
        return gettext(
            "Your password must contain at least {0} characters, "
            "including uppercase, lowercase, digits (0-9), and special characters (e.g., !@#$%^&*)."
        ).format(8)
