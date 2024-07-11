from itertools import chain
from transit_odp.data_quality.tables.base import DQSWarningListBaseTable
from django.views.generic import TemplateView
from django_hosts import reverse
from django_tables2 import MultiTableMixin, SingleTableView

import config.hosts
from transit_odp.data_quality.constants import Observation
from transit_odp.data_quality.helpers import (
    convert_date_to_dmY_string,
    create_comma_separated_string,
)
from transit_odp.data_quality.models import (
    DataQualityReportSummary,
    DataQualityWarningBase,
)
from transit_odp.data_quality.tables import (
    JourneyListTable,
    TimingPatternListTable,
    WarningListBaseTable,
)
from transit_odp.dqs.models import ObservationResults
from transit_odp.dqs.constants import Checks

class SimpleDetailBaseView(TemplateView):
    """
    A simple detail view for displaying observations that
    require no map or tables.
    The view will only render the observation title, text and
    impacts details of a data_quality.constants.Observation object.
    """

    template_name = "data_quality/simple_observation_detail.html"
    data = None
    model = None

    @property
    def data(self) -> Observation:
        raise NotImplementedError("Warning detail views must have data attribute")

    def get_object(self):
        report_id = self.kwargs.get("report_id", -1)
        return self.model.objects.get(report_id=report_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "back_url": reverse(
                    "dq:overview",
                    kwargs={
                        "pk": kwargs.get("pk"),
                        "pk1": kwargs.get("pk1"),
                        "report_id": kwargs.get("report_id"),
                    },
                    host=config.hosts.PUBLISH_HOST,
                ),
                "observation": self.data,
            }
        )
        return context


class DetailBaseView(MultiTableMixin, TemplateView):
    template_name = "data_quality/observation_detail.html"
    model = None
    related_model = None
    related_object = None
    tables = []
    paginate_by = 10

    @property
    def data(self):
        raise NotImplementedError("Warning detail views must have data attribute")

    def get(self, request, *args, **kwargs):
        # add warning to view so that we can use self.warning in other methods instead
        # of repeatedly using self.get_warning() and hammering the db
        self.warning = self.get_warning()
        return super().get(request, *args, **kwargs)

    def get_warning(self):
        warning_id = self.kwargs.get("warning_pk")
        return self.model.objects.get(id=warning_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Map variables defined largely as empty strings, with values overridden
        # in views as needed for that map
        revision_id = kwargs.get("pk")
        context.update(
            {
                # for map -- empty strings passed if specific geometry not needed
                "service_pattern_id": "",
                "stop_ids": "",
                "effected_stop_ids": "",
                "service_link_ids": "",
                "api_root": reverse(
                    "dq-api:api-root",
                    host=config.hosts.PUBLISH_HOST,
                ),
                # for backlink -- inheriting views need data attribute set to
                # relevant constant
                "back_url": reverse(
                    self.data.list_url_name,
                    kwargs={
                        "pk": revision_id,
                        "pk1": kwargs.get("pk1"),
                        "report_id": kwargs.get("report_id"),
                    },
                    host=config.hosts.PUBLISH_HOST,
                ),
            }
        )
        return context

    # Hacky way of allowing one paginated and one unpaginated table in a view
    # Copied from source
    def get_table_pagination(self, table):
        """
        Return pagination options passed to `.RequestConfig`:
            - True for standard pagination (default),
            - False for no pagination,
            - a dictionary for custom pagination.

        `ListView`s pagination attributes are taken into account, if
        `table_pagination` does not define the corresponding value.

        Override this method to further customize pagination for a `View`.
        """
        # Edited line
        paginate = table.table_pagination
        if paginate is False:
            return False

        paginate = {}
        if getattr(self, "paginate_by", None) is not None:
            paginate["per_page"] = self.paginate_by
        if hasattr(self, "paginator_class"):
            paginate["paginator_class"] = self.paginator_class
        if getattr(self, "paginate_orphans", 0) != 0:
            paginate["orphans"] = self.paginate_orphans

        # table_pagination overrides any MultipleObjectMixin attributes
        if self.table_pagination:
            paginate.update(self.table_pagination)

        # we have no custom pagination settings, so just use the default.
        if not paginate and self.table_pagination is None:
            return True

        return paginate


# TODO: try using singletableview instead of multitablemixin -- might require
# excessive editing and inconsistency with other detail views
class OneTableDetailView(DetailBaseView):
    def get_tables(self):
        assert len(self.tables) == 1, "View must have one table, for timing pattern"
        table1_class = self.tables[0]
        return [
            table1_class(self.get_queryset1(), **self.get_table1_kwargs()),
        ]

    def get_queryset1(self):
        timing_pattern = self.warning.get_timing_pattern()
        timing_pattern_stops = timing_pattern.timing_pattern_stops.order_by(
            "service_pattern_stop__position"
        )
        return timing_pattern_stops.add_stop_name().add_position()

    def get_table1_kwargs(self):
        return {
            # "effected_stop_positions": self.get_effected_stop_positions(),
            # TODO: only some child views need effected stops
            # "effected_stops": self.get_effected_stops(),
            "message_segment": self.construct_shared_message_segment(),
            "vehicle_journey_start_time": self.warning.get_vehicle_journey().start_time,
        }

    def get_context_data(self, **kwargs):
        # TODO: not sure this will work, might need to move code back into view
        subtitle = self.construct_subtitle(**kwargs)
        stop_ids = self.warning.get_stop_ids()
        timing_pattern = self.warning.get_timing_pattern()

        context = super().get_context_data(**kwargs)
        context.update(
            {
                # TODO: rename these (in all detail views) because "title" is the
                # caption above the title and "subtitle" is the title itself
                "title": self.data.title,
                "subtitle": subtitle,
                "service_pattern_id": timing_pattern.service_pattern.id,
                "stop_ids": create_comma_separated_string(stop_ids),
            }
        )
        return context

    # views often used the same chunk of message in the page heading and table caption
    def construct_shared_message_segment(self):
        vehicle_journey = self.warning.get_vehicle_journey()
        start_time = vehicle_journey.start_time.strftime("%H:%M")
        service_pattern = vehicle_journey.timing_pattern.service_pattern
        from_stop = service_pattern.service_pattern_stops.earliest("position").stop.name

        # TODO: stop using arbitrary date
        try:
            date = vehicle_journey.dates[0]
            date = convert_date_to_dmY_string(date)
        except IndexError:
            date = "unknown date"
        finally:
            return f"{start_time} from {from_stop} on {date}"

    # page heading (currently "subtitle" in context) often contains the
    # shared_message_segment plus text relevant
    # to the warning but is occasionally a completely custom message
    def construct_subtitle(self, **kwargs):
        if "subtitle" in kwargs:
            subtitle = kwargs.pop("subtitle")
        else:
            # use subtitle_end if available or fallback to default
            subtitle_end = kwargs.pop("subtitle_end", "has a data quality warning.")
            subtitle = "{} {}".format(
                self.construct_shared_message_segment(),
                subtitle_end,
            )
        return subtitle


class TwoTableDetailView(DetailBaseView):
    def get_tables(self):
        # This style of detail page has two tables: timing pattern and vehicle journeys
        assert (
            len(self.tables) == 2
        ), "View must have two tables, for timing pattern and vehicle journeys"
        table1_class = self.tables[0]
        table2_class = self.tables[1]
        return [
            table1_class(self.get_queryset1(), **self.get_table1_kwargs()),
            table2_class(self.get_queryset2(), **self.get_table2_kwargs()),
        ]

    def get_queryset1(self):
        timing_pattern = self.warning.get_timing_pattern()
        timing_pattern_stops = timing_pattern.timing_pattern_stops.order_by(
            "service_pattern_stop__position"
        )
        return timing_pattern_stops.add_stop_name().add_position()

    # largely duplicates method from OneTableDetailView but not sure we want to
    # inherit from that
    def get_table1_kwargs(self):
        return {
            "effected_stop_positions": self.warning.get_effected_stop_positions(),
            "effected_stops": self.warning.get_effected_stops(),
        }

    def get_queryset2(self):
        vehicle_journeys = self.warning.get_vehicle_journeys().order_by("start_time")
        return vehicle_journeys.add_line_name().add_first_stop()

    def get_table2_kwargs(self):
        return {}

    # not currently used
    # def get_total_distance_between_stops(self):
    #     total = 0
    #     for link in self.warning.service_links.select_related("service_link"):
    #         total += link.geometry.length

    def get_earliest_vehicle_journey_date(self, vehicle_journeys):
        nested_list = [vj.dates for vj in vehicle_journeys]
        # more efficient than using list comprehension to flatten the nested list
        dates = list(chain.from_iterable(nested_list))
        try:
            date = min(dates)
        except ValueError:
            date = None
        return date

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vehicle_journeys = self.warning.get_vehicle_journeys()
        # For text above table 2
        context["start_date"] = self.get_earliest_vehicle_journey_date(vehicle_journeys)
        context["number_of_journeys"] = vehicle_journeys.count()

        # For map
        stop_ids = self.warning.get_stop_ids()
        effected_stop_ids = self.warning.get_effected_stop_ids()
        timing_pattern = self.warning.get_timing_pattern()
        context.update(
            {
                "service_pattern_id": timing_pattern.service_pattern.id,
                "stop_ids": create_comma_separated_string(stop_ids),
                "effected_stop_ids": create_comma_separated_string(effected_stop_ids),
            }
        )
        return context


class WarningListBaseView(SingleTableView):
    template_name = "data_quality/warning_list.html"
    table_class: WarningListBaseTable
    model: DataQualityWarningBase
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["impacts"] = self.data.impacts
        return context

    def get_queryset(self):
        report_id = self.kwargs.get("report_id")
        return self.model.objects.select_related(
            "report__revision__dataset__organisation"
        ).filter(report_id=report_id)

    def get_table_kwargs(self):
        report_id = self.kwargs.get("report_id")
        try:
            summary = DataQualityReportSummary.objects.get(report_id=report_id)
            count = summary.data[self.model.__name__]
        except (KeyError, DataQualityReportSummary.DoesNotExist):
            count = self.object_list.filter(report_id=report_id).count()
        finally:
            return {"count": count}


class TimingPatternsListBaseView(WarningListBaseView):
    table_class = TimingPatternListTable

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs.update({"message_col_verbose_name": "Timing pattern"})
        return kwargs


class JourneyListBaseView(WarningListBaseView):
    table_class = JourneyListTable

    def get_table_kwargs(self):
        kwargs = super().get_table_kwargs()
        kwargs.update({"message_col_verbose_name": "Journey"})
        return kwargs


class DQSWarningListBaseView(SingleTableView):
    template_name = "data_quality/warning_list.html"
    table_class = DQSWarningListBaseTable
    model = ObservationResults
    paginate_by = 10
    check: Checks = Checks.DefaultCheck

    def get_queryset(self):

        report_id = self.kwargs.get("report_id")
        revision_id = self.kwargs.get("pk")
        print(
            f"Calling DQS Warning List base view: {report_id}, {revision_id}, {self.check}"
        )
        return self.model.objects.get_observations(report_id, self.check, revision_id)

    def get_table_kwargs(self):
        pass
