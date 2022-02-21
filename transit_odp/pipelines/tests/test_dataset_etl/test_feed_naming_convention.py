import pathlib

import dateutil
import factory
import pytest

from transit_odp.naptan.factories import LocalityFactory, StopPointFactory
from transit_odp.organisation.constants import FeedStatus
from transit_odp.organisation.factories import DatasetRevisionFactory
from transit_odp.pipelines.factories import DatasetETLTaskResultFactory
from transit_odp.pipelines.pipelines.dataset_etl.data_loader import DataLoader
from transit_odp.pipelines.pipelines.dataset_etl.feed_parser import FeedParser
from transit_odp.xmltoolkit.xml_toolkit import XmlToolkit

HERE = pathlib.Path(__file__)


def set_up_xml_file(counts, kwarg1, kwarg2, kwarg3):
    """
    Sets up the XML file for the fixtures. Creates groups of
    localities.
    :param counts: tuple of counts used by create batch, ie (5,4,2).
    sum must be 11 and not contain zero
    :param kwarg1: kwargs create_batch for 1st locality group
    :param kwarg2: kwargs create_batch for 2st locality group
    :param kwarg3: kwargs create_batch for 3st locality group
    :return: None
    """
    assert len(counts) == 3, "There are 3 groups so need 3 counts"
    assert sum(counts) == 11, "Sum of counts must be 11"
    assert 0 not in counts, "a group cannot have a 0 count"

    count1, count2, count3 = counts
    test_dir = HERE.parent
    test_file = test_dir.joinpath("data/test.xml")
    # NB: there are 11 stops in the test file

    localities = LocalityFactory.create_batch(count1, **kwarg1)
    localities += LocalityFactory.create_batch(count2, **kwarg2)
    localities += LocalityFactory.create_batch(count3, **kwarg3)

    xmltoolkit = XmlToolkit({"x": "http://www.transxchange.org.uk/"})
    doc, result = xmltoolkit.parse_xml_file(str(test_file))
    _stop_points = xmltoolkit.get_elements(
        doc, "/x:TransXChange/x:StopPoints/x:AnnotatedStopPointRef"
    )

    for index, stop in enumerate(_stop_points):
        atco = xmltoolkit.get_child_text(stop, "x:StopPointRef")
        StopPointFactory.create(atco_code=atco, locality=localities[index])


@pytest.fixture
def naptan_data_matching_xml(transactional_db):
    set_up_xml_file((5, 4, 2), {"name": "aton"}, {"name": "beton"}, {})


@pytest.fixture
def equal_districts(transactional_db):
    set_up_xml_file((5, 5, 1), {"name": "aton"}, {"name": "beton"}, {})


@pytest.fixture
def blank_district_naptan_data_matching_xml(transactional_db):
    set_up_xml_file((5, 4, 2), {"name": ""}, {"name": ""}, {"name": ""})


def setup_feed_parser(test_file, feed_name="tmpname", org_name="org"):
    """
    sets up the feed parser with test_file loaded in revision
    :param test_file: file under test, comes from fixture
    :param feed_name: name of feed not really important
    :param org_name: name of organisation defaults to "org" set to None
    to use factory-boy generated value
    :return:
    """
    test_dir = HERE.parent
    test_file_dir = test_dir.joinpath("data")
    test_file = test_file_dir.joinpath(test_file)

    revision_kwargs = {
        "status": FeedStatus.pending.value,
        "name": feed_name,
    }

    org_name and revision_kwargs.update({"dataset__organisation__name": org_name})

    revision = DatasetRevisionFactory(**revision_kwargs)
    revision.associate_file(str(test_file))
    revision.save()

    feed_progress = DatasetETLTaskResultFactory.create(revision=revision)

    return FeedParser(revision, feed_progress)


@pytest.mark.parametrize(
    "test_file, expected",
    (("test.xml", "org_aton_1A_20181009"), ("2lines.zip", "org_aton_beton_20181009")),
    ids=["single line", "multiple lines"],
)
def test_end_to_end(naptan_data_matching_xml, test_file, expected):

    feed_parser = setup_feed_parser(test_file)
    feed_parser.index_feed()
    assert feed_parser.revision.name == expected


@pytest.mark.skip
@pytest.mark.parametrize("execution_number", range(5))
def test_equal_districts_give_same_name(execution_number, equal_districts):
    """Runs the end to end test 5 times to make sure names are consistent"""
    feed_parser = setup_feed_parser("test.xml")
    feed_parser.index_feed()
    # N.B aton and beton both have 5
    assert feed_parser.revision.name.endswith("aton_1A_20181009")


@pytest.mark.parametrize(
    "test_file, expected",
    (
        ("test.xml", "org_unknown_1A_20181009"),
        ("2lines.zip", "org_unknown_unknown_20181009"),
    ),
    ids=[
        "single line with unknown districts",
        "multiple lines with unknown districts (V.Unlikely)",
    ],
)
def test_end_to_end_with_blank_districts(
    blank_district_naptan_data_matching_xml, test_file, expected
):

    feed_parser = setup_feed_parser(test_file)
    feed_parser.index_feed()
    assert feed_parser.revision.name == expected


@pytest.mark.parametrize(
    "clashing_name, expected",
    (
        ("org_aton_1A_20181009", "org_aton_1A_20181009_1"),
        ("org_aton_1A_20181009_1", "org_aton_1A_20181009_2"),
    ),
    ids=["first clash", "second clash"],
)
def test_single_line_name_clashes(transactional_db, clashing_name, expected):

    feed_parser = setup_feed_parser("test.xml")

    DatasetRevisionFactory(
        dataset__organisation=feed_parser.revision.dataset.organisation,
        status="live",
        name=clashing_name,
    )
    data_loader = DataLoader(feed_parser)
    name = data_loader.create_feed_name(
        ["aton", "beton"], dateutil.parser.parse("20181009"), 1, "1A"
    )
    assert name == expected


@pytest.mark.parametrize(
    "clashing_name, expected",
    (
        ("org_aton_beton_20181009", "org_aton_beton_20181009_1"),
        ("org_aton_beton_20181009_1", "org_aton_beton_20181009_2"),
    ),
    ids=["first clash", "second clash"],
)
def test_multiple_line_name_clashes(transactional_db, clashing_name, expected):

    feed_parser = setup_feed_parser("2lines.zip")
    DatasetRevisionFactory(
        dataset__organisation=feed_parser.revision.dataset.organisation,
        status="live",
        name=clashing_name,
    )
    data_loader = DataLoader(feed_parser)
    name = data_loader.create_feed_name(
        ["aton", "beton"], dateutil.parser.parse("20181009"), 2, "1A,Citi3"
    )
    assert name == expected


def test_10_name_clashes(transactional_db):
    feed_parser = setup_feed_parser("test.xml")
    DatasetRevisionFactory.reset_sequence(0)
    DatasetRevisionFactory.create_batch(
        13,
        dataset__organisation=feed_parser.revision.dataset.organisation,
        status="live",
        name=factory.sequence(
            lambda n: "org_TheNorth_1A_20181009"
            if n == 0
            else f"org_TheNorth_1A_20181009_{n}"
        ),
    )
    data_loader = DataLoader(feed_parser)
    name = data_loader.create_feed_name(
        ["TheNorth", "verynorth"], dateutil.parser.parse("20181009"), 1, "1A"
    )
    assert name == "org_TheNorth_1A_20181009_13"


def test_nasty_underscores_in_names(transactional_db):
    feed_parser = setup_feed_parser("test.xml")
    DatasetRevisionFactory.create(
        dataset__organisation=feed_parser.revision.dataset.organisation,
        status="live",
        name="org_at_on_1A_20181009",
    )
    data_loader = DataLoader(feed_parser)
    name = data_loader.create_feed_name(
        ["at_on", "be_ton"], dateutil.parser.parse("20181009"), 1, "1A"
    )
    assert name == "org_at_on_1A_20181009_1"


def test_name_second_name_clash_with_absent_first(transactional_db):
    """Unlikely event that the first name is deleted from the database
    after the second is created"""
    feed_parser = setup_feed_parser("test.xml")
    DatasetRevisionFactory.create(
        dataset__organisation=feed_parser.revision.dataset.organisation,
        status="live",
        name="org_aton_1A_20181009_1",
    )
    data_loader = DataLoader(feed_parser)
    name = data_loader.create_feed_name(
        ["aton", "beton"], dateutil.parser.parse("20181009"), 1, "1A"
    )
    assert name == "org_aton_1A_20181009_2"
