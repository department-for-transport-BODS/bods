import pytest
from django.core.exceptions import ValidationError

from transit_odp.common import validators
from transit_odp.common.validators import check_banned_words, validate_profanity


class TestValidateProfanity:
    def test_profanity_error_raised(self):
        # Setup
        text = "ar5e"

        # Test
        with pytest.raises(ValidationError) as e:
            validate_profanity(text)
        assert e.value.message == "Profane words are not allowed"
        assert e.value.code == "profanity"

    def test_common_profanity_is_rejected(self):
        with pytest.raises(ValidationError, match="Profane words are not allowed"):
            validate_profanity("This is ar5e")

    def test_allowlisted_word_is_accepted(self, monkeypatch):
        monkeypatch.setattr(validators, "ALLOWED_PROFANITY_WORDS", {"shit"})
        monkeypatch.setattr(validators, "_profanity_configured", False)
        monkeypatch.setattr(validators, "_profanity_whitelist", None)

        validate_profanity("This is shit")

    def test_check_banned_words_called(self, mocker):
        """Tests profanities are checked by the library."""
        # Setup
        mocked = mocker.patch(
            "transit_odp.common.validators.check_banned_words", return_value=False
        )

        # Test
        validate_profanity("ar5e")

        # Assert
        mocked.assert_called_once_with("ar5e")

    def test_check_banned_words(self):
        assert check_banned_words("ar5e") is True
