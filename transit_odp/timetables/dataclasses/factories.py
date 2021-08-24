from datetime import date, datetime

import pytz
from factory import Factory, SubFactory

from .transxchange import Header, Line, Operator, Service, TXCFile


class HeaderFactory(Factory):
    class Meta:
        model = Header

    revision_number = "0"
    schema_version = "2.4"
    modification = "new"
    creation_datetime = datetime.now(tz=pytz.UTC)
    modification_datetime = datetime.now(tz=pytz.UTC)
    filename = "transxchange.xml"


class OperatorFactory(Factory):
    class Meta:
        model = Operator

    national_operator_code = "ABC"
    operator_short_name = "ABC Buses"
    licence_number = "AB1234576"


class LineFactory(Factory):
    class Meta:
        model = Line

    line_name = "Line1"


class ServiceFactory(Factory):
    class Meta:
        model = Service

    operating_period_start_date = date(2021, 1, 1)
    operating_period_end_date = date(2022, 1, 1)
    public_use = True
    service_code = "A1"
    lines = [LineFactory()]


class TXCFileFactory(Factory):
    class Meta:
        model = TXCFile

    header = SubFactory(HeaderFactory)
    operator = SubFactory(OperatorFactory)
    service = SubFactory(ServiceFactory)
    service_code = "A1"
