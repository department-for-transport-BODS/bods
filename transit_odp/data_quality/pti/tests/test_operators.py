import pytest

from transit_odp.data_quality.pti.factories import (
    ObservationFactory,
    RuleFactory,
    SchemaFactory,
)
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator


@pytest.mark.parametrize(
    "operators,expected", [(["1", "2"], False), (["1"], True), ([], False)]
)
def test_count_operators(operators, expected):

    xml = """<Operators>{0}</Operators>"""

    operator = """
    <Operator id="{0}">
        <NationalOperatorCode>ACO</NationalOperatorCode>
        <OperatorCode>ACO</OperatorCode>
        <OperatorShortName>ACO Buses</OperatorShortName>
        <OperatorNameOnLicence>Ancient Crowded Omnibuses Ltd.</OperatorNameOnLicence>
    </Operator>
    """
    operators = [operator.format(o) for o in operators]
    operators = "\n".join(operators)
    xml = xml.format(operators)
    context = "//x:Operators"
    rule = "count(x:Operator) = 1"

    rules = [RuleFactory(test=rule)]
    observation = ObservationFactory(context=context, rules=rules)
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    xml = TXCFile(xml)
    is_valid = pti.is_valid(xml)
    assert is_valid == expected


@pytest.mark.parametrize(
    "operators,expected", [(["1", "2"], False), (["1"], False), ([], True)]
)
def test_count_licensed_operators(operators, expected):
    lic_opp = """
    <LicensedOperator
         id="{}"
         CreationDateTime="2004-12-17T09:30:47-05:00"
         ModificationDateTime="2004-12-17T09:30:47-05:00"
         Modification="revise"
         RevisionNumber="3"
         Status="active"
    >
      <NationalOperatorCode>O1</NationalOperatorCode>
      <OperatorCode>Smoo</OperatorCode>
      <OperatorShortName>Smooth Buses</OperatorShortName>
      <OperatorNameOnLicence>Smooth Buses</OperatorNameOnLicence>
      <TradingName>Smooth Buses Ltd</TradingName>
      <LicenceNumber>PB0000001</LicenceNumber>
      <LicenceClassification>standardNational</LicenceClassification>
      <EmailAddress>info@smoothbus.com</EmailAddress>
    </LicensedOperator>
    """

    operator = """
    <Operators>
        <Operator id="O2">
            <OperatorShortName>Smart Buses</OperatorShortName>
            <OperatorNameOnLicence>SmartB</OperatorNameOnLicence>
            <TradingName>Smart Buses UK Ltd</TradingName>
            <LicenceNumber>PB0000052</LicenceNumber>
            <LicenceClassification>standardNational</LicenceClassification>
            <EmailAddress>fred@smartbus.org.uk</EmailAddress>
        </Operator>
        {}
    </Operators>
    """
    lic_opp = [lic_opp.format(o) for o in operators]
    lic_opp = "\n".join(lic_opp)
    operator = operator.format(lic_opp)
    context = "//x:Operators"
    rule = "count(x:LicensedOperator) = 0"
    rules = [RuleFactory(test=rule)]
    observation = ObservationFactory(context=context, rules=rules)
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    xml = TXCFile(operator)
    is_valid = pti.is_valid(xml)
    assert is_valid == expected


@pytest.mark.parametrize(
    "no_of_registrations,expected", [(2, False), (0, True), (1, False)]
)
def test_count_registration_groups(no_of_registrations, expected):
    txc = """
    <TransXChange>
        <Routes>
            <Route id="R_1">
                <Description xml:lang="en">Grub Street to Howard's end</Description>
                <RouteSectionRef>RS_1</RouteSectionRef>
            </Route>
        </Routes>
        {}
    </TransXChange>
    """

    reg_groups = """
        <Registration>
          <ServiceRef>SV_1</ServiceRef>
          <SubmissionDate>2004-11-04</SubmissionDate>
          <ApplicationClassification>new</ApplicationClassification>
          <VariationNumber>1</VariationNumber>
        </Registration>
    """

    registrations_inner = "\n".join([reg_groups for _ in range(no_of_registrations)])
    reg_groups = (
        "<Registrations>{}</Registrations>".format(registrations_inner)
        if registrations_inner
        else registrations_inner
    )
    txc = txc.format(reg_groups)
    context = "x:TransXChange"
    rule = "count(x:Registrations) = 0"
    rules = [RuleFactory(test=rule)]
    observation = ObservationFactory(context=context, rules=rules)
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(txc)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    "garages,expected", [(["1", "2"], False), (["1"], True), ([], False)]
)
def test_correct_number_of_garage_codes(garages, expected):

    xml = """<Garages>
                <Garage>
                    {}
                    <GarageName>String</GarageName>
                    <ContactNumber>
                        <TelNationalNumber>02072699895</TelNationalNumber>
                    </ContactNumber>
                </Garage>
            </Garages>
         """

    garage = "<GarageCode>{}</GarageCode>"
    garages = [garage.format(o) for o in garages]
    garages = "\n".join(garages)
    xml = xml.format(garages)
    context = "//x:Garages/x:Garage"
    rule = "count(x:GarageCode) = 1"

    rules = [RuleFactory(test=rule)]
    observation = ObservationFactory(context=context, rules=rules)
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc_path = TXCFile(xml)
    is_valid = pti.is_valid(txc_path)
    assert is_valid == expected
