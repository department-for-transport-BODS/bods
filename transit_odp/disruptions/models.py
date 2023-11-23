from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField
from transit_odp.common.fields import CallableStorageFileField
from transit_odp.disruptions.storage import get_sirisx_storage


class DisruptionsDataArchive(models.Model):
    created = CreationDateTimeField(_("created"))
    last_updated = ModificationDateTimeField(_("last_updated"))
    data = CallableStorageFileField(
        storage=get_sirisx_storage,
        help_text=_("A zip file containing an up to date SIRI-SX XML."),
    )

    class Meta:
        get_latest_by = "-created"
        ordering = ("-created",)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(created={self.created!r}, "
            f"last_updated={self.last_updated!r}, data={self.data.name!r}, "
            f"data_format={self.data_format!r})"
        )
