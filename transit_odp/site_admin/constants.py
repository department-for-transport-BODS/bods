from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ArchiveCategory(TextChoices):
    OPERATIONAL_METRICS = ("operational_metrics", _("Operational Metrics"))
    DATA_CATALOGUE = ("data_catalogue", _("Data Catalogue"))


ARCHIVE_CATEGORY_FILENAME = {
    ArchiveCategory.OPERATIONAL_METRICS.value: "operationalexports.zip",
    ArchiveCategory.DATA_CATALOGUE.value: "bodsdatacatalogue.zip",
}

OperationalMetrics = ArchiveCategory.OPERATIONAL_METRICS.value
DataCatalogue = ArchiveCategory.DATA_CATALOGUE.value
