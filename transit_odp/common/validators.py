from better_profanity import profanity
from django.core.exceptions import ValidationError

ALLOWED_PROFANITY_WORDS = set()
_profanity_configured = False
_profanity_whitelist = None


def _configure_profanity():
    global _profanity_configured, _profanity_whitelist

    whitelist = sorted(ALLOWED_PROFANITY_WORDS)
    if _profanity_configured and _profanity_whitelist == whitelist:
        return profanity

    profanity.load_censor_words(whitelist_words=list(whitelist))
    _profanity_whitelist = whitelist
    _profanity_configured = True

    return profanity


def check_banned_words(text: str) -> bool:
    """Return True when the text contains a word from the profanity library."""
    return _configure_profanity().contains_profanity(text)


def validate_profanity(text: str) -> None:
    """Validate that text does not contain profanities."""
    if check_banned_words(text):
        raise ValidationError("Profane words are not allowed", code="profanity")
