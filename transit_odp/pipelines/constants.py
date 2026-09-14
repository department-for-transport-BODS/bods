from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class SchemaCategory(TextChoices):
    TXC = ("txc", _("TxC"))
    TXC_2_4_1 = ("txc241", _("TxC 2.4.1"))
    NETEX = ("netex", _("NeTeX"))


SCHEMA_DIR = "/tmp/schemas"
