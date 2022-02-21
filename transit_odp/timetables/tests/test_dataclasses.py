import pytest

from transit_odp.data_quality.pti.tests.conftest import TXCFile
from transit_odp.timetables.dataclasses.transxchange import Operator, Service
from transit_odp.timetables.transxchange import TransXChangeDocument


def test_operator_from_no_operators():
    operators = "<Operators></Operators>"
    xml = TXCFile(operators)
    doc = TransXChangeDocument(xml)
    operator = Operator.from_txc_document(doc)
    assert operator.national_operator_code == ""
    assert operator.licence_number == ""
    assert operator.operator_short_name == ""


def test_operator_from_licensed_operator():
    operators = """
    <Operators>
        <LicensedOperator id="O1">
            <NationalOperatorCode>ABC</NationalOperatorCode>
            <OperatorCode>ABC</OperatorCode>
            <OperatorShortName>ABC Buses</OperatorShortName>
            <OperatorNameOnLicence>ABC Buses and Services</OperatorNameOnLicence>
            <LicenceNumber>AB1234576</LicenceNumber>
            <LicenceClassification>standardNational</LicenceClassification>
            <EnquiryTelephoneNumber>
                <TelNationalNumber>0207123456</TelNationalNumber>
            </EnquiryTelephoneNumber>
            <ContactTelephoneNumber>
                <TelNationalNumber>0207654321</TelNationalNumber>
            </ContactTelephoneNumber>
            <EmailAddress>enquires@ABCBuses.com</EmailAddress>
        </LicensedOperator>
    </Operators>
    """
    xml = TXCFile(operators)
    doc = TransXChangeDocument(xml)
    operator = Operator.from_txc_document(doc)
    assert operator.national_operator_code == "ABC"
    assert operator.licence_number == "AB1234576"
    assert operator.operator_short_name == "ABC Buses"


def test_operator_from_vanilla_operator():
    operators = """
    <Operators>
        <Operator id="O1">
            <NationalOperatorCode>ACO</NationalOperatorCode>
            <OperatorCode>ACO</OperatorCode>
            <OperatorShortName>ACO Buses</OperatorShortName>
            <OperatorNameOnLicence>Ancient Crowded Ltd.</OperatorNameOnLicence>
            <LicenceNumber>AC1234567</LicenceNumber>
            <LicenceClassification>standardNational</LicenceClassification>
            <EnquiryTelephoneNumber>
                <TelNationalNumber>020712346</TelNationalNumber>
            </EnquiryTelephoneNumber>
            <ContactTelephoneNumber>
                <TelNationalNumber>0207666543</TelNationalNumber>
            </ContactTelephoneNumber>
            <EmailAddress>enquiries@acobuses.co.uk</EmailAddress>
        </Operator>
    </Operators>
    """
    xml = TXCFile(operators)
    doc = TransXChangeDocument(xml)
    operator = Operator.from_txc_document(doc)
    assert operator.national_operator_code == "ACO"
    assert operator.licence_number == "AC1234567"
    assert operator.operator_short_name == "ACO Buses"


@pytest.mark.parametrize(
    ("origin", "destination"),
    [
        ("Cobholm", "Cliff Park Academy"),
        ("", "Cliff Park Academy"),
        ("Cobholm", ""),
        ("", ""),
    ],
)
def test_parse_standard_service_origin_destination(origin, destination):
    services = f"""
    <Services>
        <Service>
            <ServiceCode>PF0000323:418</ServiceCode>
            <PrivateCode>FECS_921</PrivateCode>
            <TicketMachineServiceCode>921</TicketMachineServiceCode>
            <RegisteredOperatorRef>O1</RegisteredOperatorRef>
            <PublicUse>true</PublicUse>
            <StandardService>
                <Origin>{origin}</Origin>
                <Destination>{destination}</Destination>
            </StandardService>
        </Service>
    </Services>
    """
    xml = TXCFile(services)
    doc = TransXChangeDocument(xml)
    service = Service.from_txc_document(doc)
    assert service.origin == origin
    assert service.destination == destination


@pytest.mark.parametrize(
    ("origin", "destination"),
    [
        ("Cobholm", "Cliff Park Academy"),
        ("", "Cliff Park Academy"),
        ("Cobholm", ""),
        ("", ""),
    ],
)
def test_parse_flexible_service_origin_destination(origin, destination):
    services = f"""
    <Services>
        <Service>
            <ServiceCode>PF0000323:418</ServiceCode>
            <PrivateCode>FECS_921</PrivateCode>
            <TicketMachineServiceCode>921</TicketMachineServiceCode>
            <RegisteredOperatorRef>O1</RegisteredOperatorRef>
            <PublicUse>true</PublicUse>
            <FlexibleService>
                <Origin>{origin}</Origin>
                <Destination>{destination}</Destination>
            </FlexibleService>
        </Service>
    </Services>
    """
    xml = TXCFile(services)
    doc = TransXChangeDocument(xml)
    service = Service.from_txc_document(doc)
    assert service.origin == origin
    assert service.destination == destination


def test_multiple_services():
    services = """
    <Services>
        <Service>
            <ServiceCode>PF0000323:418</ServiceCode>
            <PrivateCode>FECS_921</PrivateCode>
            <TicketMachineServiceCode>921</TicketMachineServiceCode>
            <RegisteredOperatorRef>O1</RegisteredOperatorRef>
            <PublicUse>true</PublicUse>
            <StandardService>
                <Origin>Neverland</Origin>
                <Destination>Narnia</Destination>
            </StandardService>
        </Service>
        <Service>
            <ServiceCode>PF0000323:419</ServiceCode>
            <PrivateCode>FECS_922</PrivateCode>
            <TicketMachineServiceCode>922</TicketMachineServiceCode>
            <RegisteredOperatorRef>O1</RegisteredOperatorRef>
            <PublicUse>true</PublicUse>
            <StandardService>
                <Origin>Milton Keynes</Origin>
                <Destination>Bedford</Destination>
            </StandardService>
        </Service>
    </Services>
    """
    xml = TXCFile(services)
    doc = TransXChangeDocument(xml)

    service = Service.from_txc_document(doc)
    assert service.origin == "Neverland"
    assert service.destination == "Narnia"
