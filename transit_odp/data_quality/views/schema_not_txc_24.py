from transit_odp.data_quality.constants import SchemaNotTXC24
from transit_odp.data_quality.models.warnings import SchemaNotTXC24Warning
from transit_odp.data_quality.views.base import SimpleDetailBaseView


class SchemaNotTXC24DetailView(SimpleDetailBaseView):
    data = SchemaNotTXC24
    model = SchemaNotTXC24Warning
