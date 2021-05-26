from django.utils import timezone


def localize_datetime_and_convert_to_string(datetime_object):
    # convert datetime using default TIME_ZONE in settings.py
    localized_datetime = timezone.localtime(datetime_object)
    datetime_string_format = "%d-%m-%Y %H:%M"
    return localized_datetime.strftime(datetime_string_format)
