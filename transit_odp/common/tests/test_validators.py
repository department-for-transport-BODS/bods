import os

import pandas as pd
import pytest
from config.settings.base import APPS_DIR
from django.core.exceptions import ValidationError

from transit_odp.common.validators import check_banned_words, validate_profanity


class TestValidateProfanity:
    swears = pd.read_csv(
        os.path.join(APPS_DIR, "common/swear_word_list.csv"), names=["word"]
    )

    def test_profanity_error_raised(self):
        # Setup
        text = "Shit"

        # Test
        with pytest.raises(ValidationError) as e:
            validate_profanity(text)
        assert e.value.message == "Profane words are not allowed"
        assert e.value.code == "profanity"

    def test_check_banned_words_called(self, mocker):
        """Tests banned_words are checked for less obvious profanities"""
        # Setup
        mocked = mocker.patch(
            "transit_odp.common.validators.check_banned_words", return_value=False
        )

        # Test
        validate_profanity("ar5e")

        # Assert
        mocked.assert_called_once_with("ar5e")

    def test_check_banned_words(self):
        # Test
        assert check_banned_words("ar5e") is True
