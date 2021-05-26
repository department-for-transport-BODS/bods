import django_tables2 as tables


class GovUkTable(tables.Table):
    class Meta:
        template_name = "common/custom_govuk_table.html"

        # We have to set the header attributes here rather than in the template.
        # Setting in the template prevents the attrs mechanism working, which
        # we need on a per-column basis for some columns.
        attrs = {"th": {"class": "govuk-table__header"}}

        default = ""

    # This can be used to add pagination to top, bottom or both
    pagination_bottom = True


class TruncatedTextColumn(tables.Column):
    """
    A Column to limit to specified default 40 number of characters and
    add an ellipsis.
    """

    def __init__(self, *args, **kwargs):
        limit = kwargs.pop("limit", None)
        self.limit = limit or 40
        super().__init__(*args, **kwargs)

    def render(self, value):
        if value is not None and len(value) > self.limit:
            upper = self.limit - 1
            return value[0:upper] + "..."
        return str(value)
