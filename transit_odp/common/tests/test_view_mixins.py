import pytest
from django.core.exceptions import ImproperlyConfigured

from transit_odp.common.view_mixins import RangeFilterContentMixin, RangeFilterListView
from transit_odp.common.view_models import RangeFilter
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.organisation.models import Organisation

pytestmark = pytest.mark.django_db


class TestRangeFilterContentMixin:
    def test_get_lookup_raises_when_improperly_configured(self):
        """Tests get_lookup will raise if lookup is not overridden"""
        # Assert
        with pytest.raises(ImproperlyConfigured):
            view = RangeFilterContentMixin()
            view.get_lookup()

    def test_get_lookup_returns_lookup(self):
        """Tests get_lookup returns lookup"""
        # Set up
        view = RangeFilterContentMixin()
        view.lookup = "name__iregex"

        # Test
        lookup = view.get_lookup()

        # Assert
        assert lookup == "name__iregex"

    def test_get_default_range(self):
        """Tests get_default_range returns the first element in ranges"""
        # Set up
        view = RangeFilterContentMixin()
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]

        # Test
        default_range = view.get_default_range()

        # Assert
        assert default_range == "a-f"

    def test_get_filter_param_returns_default(self, request_factory):
        """
        Tests get_filter_param returns default if request doesn't contain
        query parameter"""
        # Set up
        view = RangeFilterContentMixin()
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]

        request = request_factory.get("fake-url/")
        view.request = request

        # Test
        filter_param = view.get_filter_param()

        # Assert
        assert filter_param == "a-f"

    def test_get_filter_param_returns_get_data(self, request_factory):
        """Tests get_filter_param extracts filter_param from query parameter"""
        # Set up
        view = RangeFilterContentMixin()
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]

        request = request_factory.get("fake-url/", data={"range": "g-l"})
        view.request = request

        # Test
        filter_param = view.get_filter_param()

        # Assert
        assert filter_param == "g-l"

    def test_get_filter_param_custom_query_param(self, request_factory):
        """Tests get_filter_param extracts query param using overridable key"""
        # Set up
        view = RangeFilterContentMixin()
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]

        request = request_factory.get("fake-url/", data={"custom-param": "g-l"})
        view.request = request

        # Test
        view.query_param = "custom-param"
        filter_param = view.get_filter_param()

        # Assert
        assert filter_param == "g-l"

    def test_get_filter_param_returns_default_when_invalid(self, request_factory):
        """Tests get_filter_param returns the default range if query param is invalid"""
        # Set up
        view = RangeFilterContentMixin()
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]

        request = request_factory.get("fake-url/", data={"range": "1-10"})
        view.request = request

        # Test
        filter_param = view.get_filter_param()

        # Assert
        assert filter_param == "a-f"

    def test_apply_range_filter(self):
        """Tests apply_range_filter filters queryset using lookup and filter_param"""
        # Set up
        view = RangeFilterContentMixin()
        view.lookup = "name__iregex"
        filter_param = "a-f"

        # create some test data
        expected = [OrganisationFactory.create(name=name) for name in list("abc")]
        [OrganisationFactory.create(name=name) for name in list("xyz")]

        qs = Organisation.objects.all()

        # Test
        filtered = view.apply_range_filter(qs, filter_param)

        # Assert
        assert list(filtered) == expected

    def test_get_filter_context(self, mocker):
        """Tests get_filter_context builds filter context:

        - the range contains 'display', a display-friendly value
        - ranges with no results have disabled=True
        """
        # Set up
        view = RangeFilterContentMixin()
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]
        view.lookup = "name__iregex"

        filter_param = "a-f"
        mocked_get_filter_param = mocker.patch.object(
            view, "get_filter_param", return_value=filter_param
        )

        # create some test data
        [OrganisationFactory.create(name=name) for name in list("abc") + list("xyz")]

        qs = Organisation.objects.all()

        # Test
        context = view.get_filter_context(qs)

        # Assert
        mocked_get_filter_param.assert_called_once()

        assert context == {
            "current_range": filter_param,
            "range_filters": [
                RangeFilter(filter="a-f", display="A - F", disabled=False),
                RangeFilter(filter="g-l", display="G - L", disabled=True),
                RangeFilter(filter="m-r", display="M - R", disabled=True),
                RangeFilter(filter="s-z", display="S - Z", disabled=False),
            ],
        }


class TestRangeFilterListView:
    def test_get_context_data(self, mocker):
        # Set up
        view = RangeFilterListView()
        view.model = Organisation
        view.lookup = "name__iregex"
        view.ranges = ["a-f", "g-l", "m-r", "s-z"]

        # create some test data
        objs = [OrganisationFactory.create(name=name) for name in list("abcd")]
        [OrganisationFactory.create(name=name) for name in list("xyz")]

        filter_param = "a-f"
        mocked_get_filter_param = mocker.patch.object(
            view, "get_filter_param", return_value=filter_param
        )

        view.object_list = Organisation.objects.all()

        # Test
        context = view.get_context_data()

        # Assert
        mocked_get_filter_param.assert_called()

        assert "items_per_col" in context
        items_per_col = context["items_per_col"]

        assert len(items_per_col) == 3
        assert items_per_col[0] == [objs[0], objs[1]]
        assert items_per_col[1] == [objs[2]]
        assert items_per_col[2] == [objs[3]]

        assert "current_range" in context
        assert "range_filters" in context

    @pytest.mark.parametrize(
        "total_items,cols,items_in_col",
        [
            (1, 3, [1, 0, 0]),
            (2, 3, [1, 1, 0]),
            (3, 3, [1, 1, 1]),
            (10, 3, [4, 3, 3]),
            (11, 3, [4, 4, 3]),
        ],
    )
    def test_get_items_per_col(self, total_items, cols, items_in_col):
        # Test
        result = RangeFilterListView.get_items_per_col(total_items, cols)

        # Assert
        assert result == items_in_col

    def test_get_qs_slices(self):
        """Tests the qs is sliced up into 3 lists"""
        # Set up
        items_per_col = [4, 3, 3]
        items = list(range(10))

        # Test
        slices = RangeFilterListView.get_qs_slices(items, items_per_col)

        # Assert
        assert len(slices) == 3
        assert slices[0] == [0, 1, 2, 3]
        assert slices[1] == [4, 5, 6]
        assert slices[2] == [7, 8, 9]
