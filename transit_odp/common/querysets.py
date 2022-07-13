from django.db.models import Aggregate, CharField, Value


class GroupConcat(Aggregate):
    function = "GROUP_CONCAT"
    nane = "Group Concat"
    template = "%(function)s(%(distinct)s%(expressions)s)"
    allow_distinct = True

    def __init__(self, expression, delimiter, distinct=False, **extra):
        output_field = extra.pop("output_field", CharField())
        delimiter = Value(delimiter, CharField())
        super(GroupConcat, self).__init__(
            expression,
            delimiter,
            output_field=output_field,
            distinct="DISTINCT " if distinct else "",
            **extra
        )

    def as_postgresql(self, compiler, connection):
        self.function = "STRING_AGG"
        return super(GroupConcat, self).as_sql(compiler, connection)
