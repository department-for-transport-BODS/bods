from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class LicenceStatuses(TextChoices):
    VALID = ("valid", _("Valid"))
    CURTAILED = ("curtailed", _("Curtailed"))
    SUSPENDED = ("suspended", _("Suspended"))


class TrafficAreas(TextChoices):
    B = ("B", _("North East"))
    C = ("C", _("North West"))
    D = ("D", _("West Midlands"))
    F = ("F", _("East of England"))
    G = ("G", _("Wales"))
    H = ("H", _("West of England"))
    K = ("K", _("London and South East"))
    M = ("M", _("Scotland"))


class LicenceDescription(TextChoices):
    STANDARD_NATIONAL = ("standard national", _("Standard national"))
    STANDARD_INTERNATIONAL = ("standard international", _("Standard international"))
    RESTRICTED = ("restricted", _("Restricted"))
    SPECIAL_RESTRICTED = ("special restricted", _("Special restricted"))


class SubsidiesDescription(TextChoices):
    YES = ("Yes", _("Yes"))
    NO = ("No", _("No"))
    IN_PART = ("In Part", _("In Part"))


SCHOOL_OR_WORKS = "School or Works"
FLEXIBLE_REG = "Flexible Registration"


OTC_CSV_URL = "https://content.mgmt.dvsacloud.uk/olcs.prod.dvsa.aws/data-gov-uk-export"
CSV_FILE_TEMPLATE = "Bus_RegisteredOnly_{}.csv"
