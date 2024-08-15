import pytest
from django.test import RequestFactory
from django_hosts.resolvers import reverse

import config.hosts
from transit_odp.data_quality.helpers import create_comma_separated_string
from transit_odp.users.factories import OrgAdminFactory


def get_initialised_view(view_class, warning, add_object_list=False):
    """
    Create an instance of the specified view_class initialised with request, args,
    kwargs and (optionally) object list
    This allows testing of individual methods on the view, bringing us closer to unit
    rather than integration testing
    """
    # setup view kwargs that would normally come from url params
    # warning_pk isn't used in warning list views, but passing it here does no harm
    dataset_id = warning.report.revision.dataset_id
    warning_id = warning.id

    # django-tables2 configure function tries to access request.GET and causes
    # error if it doesn't exist.
    # get() is a convenient way of adding request.method and request.GET
    request = RequestFactory().get("some-url/")
    # ensure organisation of user matches that of warning
    request.user = OrgAdminFactory(
        organisations=(warning.report.revision.dataset.organisation,)
    )

    view = view_class()
    view.setup(
        request,
        pk=dataset_id,
        warning_pk=warning_id,
        pk1=warning.report.revision.dataset.organisation_id,
        report_id=warning.report.id,
    )

    # because we're testing in relative isolation, we must add the object_list
    # attribute ourselves
    # sometimes convenient to do so when initialising the view, but not always
    # desirable (e.g. if testing get_queryset)
    if add_object_list:
        view.object_list = view.get_queryset()

    # all detail views need access to self.warning
    view.warning = warning

    return view


# short unit tests with few (even one) assert should point very specifically to
# errors, without subsequent asserts being hidden by an early failure
class ListPageBaseTest:
    """Base class for testing Data Quality warning list pages"""

    model = None
    factory = None
    view = None
    expected_output = {}

    def test_view_uses_correct_model(self, warning):
        view = get_initialised_view(self.view, warning)
        assert view.data.model == self.model

    @pytest.mark.skip(reason="Skipping this test case until old DQS is decommissioned")
    def test_preamble_text(self, warning):
        view = get_initialised_view(self.view, warning)
        # ensure get_context_data has access to pk and warning_pk
        context = view.get_context_data(object_list=[])
        assert context["preamble"] == self.expected_output["test_preamble_text"]

    @pytest.mark.skip(reason="Skipping this test case until old DQS is decommissioned")
    def test_get_queryset_only_returns_warnings_for_this_report(
        self,
        warning,
    ):
        # create warning for different report on same dataset
        dataset = warning.report.revision.dataset
        warning2 = self.factory(report__revision__dataset=dataset)

        view = get_initialised_view(self.view, warning)
        warnings_qs = view.get_queryset()

        # get_queryset should return only the warning from the report that's id is
        # specified in kwargs
        assert warnings_qs.count() == 1
        with pytest.raises(self.model.DoesNotExist):
            warnings_qs.get(id=warning2.id)
        warnings_qs.get(id=warning.id)

    @pytest.mark.skip(reason="Skipping this test case until old DQS is decommissioned")
    def test_get_queryset_adds_correct_message_annotation(
        self,
        warning,
    ):
        view = get_initialised_view(self.view, warning)
        warnings_qs = view.get_queryset()

        from_stop_name = warning.service_links.first().from_stop.name
        to_stop_name = warning.service_links.first().to_stop.name

        expected_message = self.expected_output[
            "test_get_queryset_adds_correct_message_annotation"
        ]
        expected_message = expected_message.format(
            from_stop_name=from_stop_name, to_stop_name=to_stop_name
        )

        assert warnings_qs.first().message == expected_message

    @pytest.mark.skip(reason="Skipping this test case until old DQS is decommissioned")
    def test_get_table_creates_correct_column_headers(self, warning):
        view = get_initialised_view(self.view, warning, add_object_list=True)
        # column headers constructed from table definition, information in
        # get_table_kwargs and count of object_list
        table = view.get_table(**view.get_table_kwargs())

        headers = [column.header for column in table.columns]

        expected_output = self.expected_output[
            "test_get_table_creates_correct_column_headers"
        ]
        assert headers == expected_output


class DetailPageBaseTest:
    """Base class for testing Data Quality warning detail pages"""

    def test_view_uses_correct_model(self, warning):
        view = get_initialised_view(self.view, warning)
        assert view.data.model == self.model

    def test_service_name_used(self, warning):
        view = get_initialised_view(self.view, warning)
        # ensure get_context_data has access to pk and warning_pk
        context = view.get_context_data(**view.kwargs)

        service_name = warning.timing_pattern.service_pattern.service.name
        assert service_name in context["subtitle"]

    def test_subtitle_text(self, warning):
        view = get_initialised_view(self.view, warning)
        # ensure get_context_data has access to pk and warning_pk
        context = view.get_context_data(**view.kwargs)
        service_name = warning.timing_pattern.service_pattern.service.name
        assert context["subtitle"] == self.expected_output["test_subtitle_text"].format(
            service_name=service_name
        )

    def test_context_passed_for_map(self, warning):
        view = get_initialised_view(self.view, warning)
        # ensure get_context_data has access to pk and warning_pk
        context = view.get_context_data(**view.kwargs)

        service_pattern_id = warning.timing_pattern.service_pattern.id
        stop_ids = warning.get_stop_ids()
        effected_stop_ids = warning.get_effected_stop_ids()

        assert context["service_pattern_id"] == service_pattern_id
        assert context["stop_ids"] == create_comma_separated_string(stop_ids)
        assert context["effected_stop_ids"] == create_comma_separated_string(
            effected_stop_ids
        )
        # this map shouldn't show service links
        assert context["service_link_ids"] == ""

    def test_timing_pattern_table_caption(
        self,
        warning,
    ):
        """
        Because first_effected_stop_name and last_effected_stop_name are defined
        in the method, you can use 0, 1, or 2 of the variables in your expected
        message because str.format() won't throw an error. So 'Stop
        {first_effected_stop_name}' is fine
        """
        view = get_initialised_view(self.view, warning)
        timing_pattern_table, _ = view.get_tables()
        effected_stops = warning.get_effected_stops()

        first_effected_stop_name = effected_stops.earliest("position").name
        last_effected_stop_name = effected_stops.latest("position").name

        expected_message = self.expected_output["test_timing_pattern_table_caption"]
        expected_message = expected_message.format(
            first_effected_stop_name=first_effected_stop_name,
            last_effected_stop_name=last_effected_stop_name,
        )

        assert expected_message in timing_pattern_table.warning_message

    def test_timing_pattern_table_num_rows(self, warning):
        view = get_initialised_view(self.view, warning)
        timing_pattern_table, _ = view.get_tables()

        assert (
            len(timing_pattern_table.rows)
            == warning.timing_pattern.timing_pattern_stops.count()
        )

    def test_total_journeys_affected(self, warning):
        view = get_initialised_view(self.view, warning)
        context = view.get_context_data(**view.kwargs)

        # TimingPatternFactory default behaviour is to create 5 related VehicleJourneys
        assert context["number_of_journeys"] == 5

    # TODO
    @pytest.mark.skip(
        reason="""Test get_earliest_vehicle_journey_date helper method that's
        on the base view (in a more relevant test class)"""
    )
    def test_total_journeys_affected_from_date(self, warning, initialised_detail_view):
        pass

    def test_vehicle_journeys_table_num_rows(self, warning):
        view = get_initialised_view(self.view, warning)
        _, vehicle_journeys_table = view.get_tables()

        # TimingPatternFactory default behaviour is to create 5 related VehicleJourneys
        assert len(vehicle_journeys_table.rows) == 5

    def test_back_url_is_warning_list_page(self, warning):
        view = get_initialised_view(self.view, warning)
        context = view.get_context_data(**view.kwargs)

        expected_url = reverse(
            self.list_url_name,
            kwargs={
                "pk": warning.report.revision.dataset_id,
                "pk1": warning.report.revision.dataset.organisation_id,
                "report_id": warning.report.id,
            },
            host=config.hosts.PUBLISH_HOST,
        )

        assert context["back_url"] == expected_url
