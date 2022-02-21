import pytest

from transit_odp.data_quality.pti.factories import (
    ObservationFactory,
    RuleFactory,
    SchemaFactory,
)
from transit_odp.data_quality.pti.tests.conftest import JSONFile, TXCFile
from transit_odp.data_quality.pti.validators import PTIValidator

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "infos,expected",
    [(("true",), False), (("false",), True), ((), True)],
)
def test_notes_not_private(infos, expected):
    xml = """
    <Notes>
        <Note>
            <NoteCode>N1</NoteCode>
            <NoteText>This is a note</NoteText>
            {}
        </Note>
    </Notes>
    """
    notes_temp = "<Private>{}</Private>"
    notes_infos = [notes_temp.format(info) for info in infos]
    xml = xml.format("\n".join(notes_infos))
    txc = TXCFile(xml)

    details = (
        "Notes field is optional. But if you are including it then it is required to "
        "be in the correct structure. Here, you have an incorrect structure in 'Notes' "
        "field. The private element can only be 'False' and cannot be set to 'True'."
    )
    rule = RuleFactory(test="not(bool(.))")
    observation = ObservationFactory(
        details=details,
        context="//x:Note/x:Private",
        category="Notes",
        reference="2.4.3",
        rules=[rule],
    )
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)

    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    "chars,expected", [("This is a note", True), ("this, is bad@", False), ("", True)]
)
def test_notes_do_not_contain_forbidden_special_characters(chars, expected):
    xml = """
    <Notes>
        <Note>
            <NoteCode>N1</NoteCode>
            <NoteText>{}</NoteText>
            <Private>false</Private>
        </Note>
    </Notes>
    """
    xml = xml.format(chars) if chars else "<parent></parent>"
    txc = TXCFile(xml)

    details = (
        "Notes field is optional. But if you are including it then it is required "
        "to be in the correct structure. Here, you have an incorrect structure in "
        "'Notes' field. Please do not include any of the following characters in the "
        r"field: ,[]{}^=@:;#$£?%+<>«»\/|~_¬"
    )
    rule = RuleFactory(test="not(has_prohibited_chars(.))")
    observation = ObservationFactory(
        details=details,
        context="//x:Note/x:NoteText",
        category="Notes",
        reference="2.4.3",
        rules=[rule],
    )
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected


@pytest.mark.parametrize(
    "chars,expected",
    [("This is a note", True), ("This contains a 2020-12-10", False), ("", True)],
)
def test_notes_do_not_contain_dates(chars, expected):
    xml = """
    <Notes>
        <Note>
            <NoteCode>N1</NoteCode>
            <NoteText>{}</NoteText>
            <Private>false</Private>
        </Note>
    </Notes>
    """
    xml = xml.format(chars) if chars else "<parent></parent>"
    txc = TXCFile(xml)

    details = (
        "Notes field is optional. But if you are including it then it is required "
        "to be in the correct structure. Here, you have an incorrect structure "
        "in 'Notes' field. The field you specified contains a date, please make "
        "sure that any date/time data is not included in notes and is used in "
        "the relevant date fields."
    )
    rule = RuleFactory(test="not(contains_date(.))")
    observation = ObservationFactory(
        details=details,
        context="//x:Note/x:NoteText",
        category="Notes",
        reference="2.5",
        rules=[rule],
    )
    schema = SchemaFactory(observations=[observation])
    json_file = JSONFile(schema.json())
    pti = PTIValidator(json_file)
    is_valid = pti.is_valid(txc)
    assert is_valid == expected
