from datetime import datetime

import pytz
from factory import Factory, SubFactory

from .transxchange import Header, Operator, TXCFile


class HeaderFactory(Factory):
    class Meta:
        model = Header

    revision_number = "0"
    schema_version = "2.4"
    modification = "new"
    creation_datetime = datetime.now(tz=pytz.UTC)
    modificaton_datetime = datetime.now(tz=pytz.UTC)
    filename = "transxchange.xml"


class OperatorFactory(Factory):
    class Meta:
        model = Operator

    national_operator_code = "ABC"
    operator_short_name = "ABC Buses"
    licence_number = "AB1234576"


class TXCFileFactory(Factory):
    class Meta:
        model = TXCFile

    header = SubFactory(HeaderFactory)
    operator = SubFactory(OperatorFactory)
    service_code = "A1"
