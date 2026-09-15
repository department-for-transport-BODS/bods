from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class SchemaCategory(TextChoices):
    TXC = ("txc", _("TxC"))
    NETEX = ("netex", _("NeTeX"))


SCHEMA_DIR = "/tmp/schemas"
