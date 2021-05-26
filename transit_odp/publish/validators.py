import os

from django.core.exceptions import ValidationError


# TODO - replace this with built-in validator class, FileExtensionValidator
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = [".xml", ".txc", ".zip"]
    if not ext.lower() in valid_extensions:
        raise ValidationError(u"Provided file format is incorrect", code="invalid")
