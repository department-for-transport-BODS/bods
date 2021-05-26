import os
import string

import pandas as pd
from django.conf import settings
from django.core.exceptions import ValidationError

TRANSLATOR = str.maketrans(string.punctuation, " " * len(string.punctuation))


def get_banned_words():
    # TODO CM - What is this?
    if get_banned_words.banned_words is None:
        get_banned_words.banned_words = set(
            pd.read_csv(
                os.path.join(settings.APPS_DIR, "common/swear_word_list.csv"),
                names=["word"],
            )["word"]
        )
    return get_banned_words.banned_words


get_banned_words.banned_words = None


def check_banned_words(text: str) -> bool:
    """Checks for banned_words in `text`.

    Returns True if `text` contains a banned word, else False."""
    banned_words = get_banned_words()
    return any(word in banned_words for word in text.split())


def validate_profanity(text: str) -> None:
    """Validates text does not contain profanities"""
    text = text.lower()

    # replace punctuation with white space
    text.translate(TRANSLATOR)

    if check_banned_words(text):
        raise ValidationError("Profane words are not allowed", code="profanity")
