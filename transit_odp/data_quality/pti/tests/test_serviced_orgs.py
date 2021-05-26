import pytest

from transit_odp.data_quality.pti.factories import (
    ObservationFactory,
    RuleFactory,
    SchemaFactory,
)
from transit_odp.data_quality.pti.models import Schema
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator
from transit_odp.timetables.utils import PTI_PATH


@pytest.mark.parametrize(
    "date,provisional,expected",
    [
        ("1990-01-01", "true", False),
        ("1990-01-01", "false", True),
        ("2055-01-01", "false", True),
        ("2055-01-01", "true", True),
        ("", "true", False),
    ],
)
def test_start_date_provisional(date, provisional, expected):
    if date:
        date = "<StartDate>{0}</StartDate>".format(date)

    xml = """
    <ServicedOrganisations>
        <ServicedOrganisation>
            <WorkingDays>
                <DateRange>
                    {0}
                    <EndDate>2004-12-23</EndDate>
                    <Description>Michaelmas Term</Description>
                    <Provisional>{1}</Provisional>
                    <DateClassification>term</DateClassification>
                </DateRange>
            </WorkingDays>
        </ServicedOrganisation>
    </ServicedOrganisations>
    """
    xml = xml.format(date, provisional)

    OBSERVATION_ID = 11
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    "name,expected",
    [
        ("a", False),
        ("aardvark", True),
        ("     ", False),
        ("_     ", False),
        ("     _", False),
        ("", False),
    ],
)
def test_string_length(name, expected):
    xml = """
    <ServicedOrganisations>
        <ServicedOrganisation>
            {0}
            <WorkingDays>
                <DateRange>
                    <StartDate>2021-01-01</StartDate>
                    <EndDate>2004-12-23</EndDate>
                    <Description>Michaelmas Term</Description>
                    <Provisional>false</Provisional>
                    <DateClassification>term</DateClassification>
                </DateRange>
            </WorkingDays>
        </ServicedOrganisation>
    </ServicedOrganisations>
    """
    name_temp = "<Name>{0}</Name>" if name else ""
    name = name_temp.format(name)
    xml = xml.format(name)

    details = (
        "Serviced Organisations are optional. But if you are including "
        "it then it is required to be in the correct structure. Here, you have "
        "an incorrect structure in the 'Name' element in 'ServicedOrganisation' field. "
        "Please provide a meaningful name for the organisation composed of more "
        "than 5 characters atleast."
    )
    rules = (
        RuleFactory(test="count(x:Name) = 1"),
        RuleFactory(test="string-length(strip(x:Name)) >= 5"),
    )
    observation = ObservationFactory(
        details=details,
        context="//x:ServicedOrganisations/x:ServicedOrganisation",
        category="Serviced organisations",
        reference="3.2",
        rules=rules,
    )
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected
    assert len(pti.violations) <= 1


@pytest.mark.parametrize(
    ("start_date", "end_date", "expected"),
    [
        ("1990-01-01", "1990-02-01", True),
        ("1990-01-01", "", False),
        ("", "1990-02-01", False),
        ("", "", False),
    ],
)
def test_has_start_and_end_date(start_date, end_date, expected):
    xml = """
    <ServicedOrganisations>
        <ServicedOrganisation>
            <WorkingDays>
                <DateRange>
                    {0}
                </DateRange>
            </WorkingDays>
        </ServicedOrganisation>
    </ServicedOrganisations>
    """
    dates = ""
    if start_date:
        dates += "<StartDate>{0}</StartDate>\n".format(start_date)
    if end_date:
        dates += "<EndDate>{0}</EndDate>\n".format(end_date)
    xml = xml.format(dates)

    OBSERVATION_ID = 9
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


def test_no_holidays_false():
    xml = """
    <ServicedOrganisations>
        <ServicedOrganisation>
            <Holidays>
                <DateRange>
                    <StartDate>2004-11-01</StartDate>
                    <EndDate>2004-11-07</EndDate>
                    <Description>Autumn Half term </Description>
                    <Provisional>false</Provisional>
                    <DateClassification>holiday</DateClassification>
                </DateRange>
            </Holidays>
        </ServicedOrganisation>
    </ServicedOrganisations>
    """
    OBSERVATION_ID = 50
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]

    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert not is_valid


def test_no_holidays_true():
    xml = """
    <ServicedOrganisations>
        <ServicedOrganisation>
            <WorkingDays>
                <DateRange>
                    <StartDate>2021-01-01</StartDate>
                    <EndDate>2004-12-23</EndDate>
                    <Description>Michaelmas Term</Description>
                    <Provisional>true</Provisional>
                    <DateClassification>term</DateClassification>
                </DateRange>
            </WorkingDays>
        </ServicedOrganisation>
    </ServicedOrganisations>
    """
    OBSERVATION_ID = 50
    schema = Schema.from_path(PTI_PATH)
    observations = [o for o in schema.observations if o.number == OBSERVATION_ID]
    schema = SchemaFactory(observations=observations)
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    txc = TXCFile(xml)
    is_valid = pti.is_valid(txc)
    assert is_valid
