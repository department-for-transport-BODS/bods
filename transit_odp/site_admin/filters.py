import django_filters as filters
from django.contrib.auth import get_user_model

from transit_odp.organisation.constants import (
    ORG_ACTIVE,
    ORG_INACTIVE,
    ORG_NOT_YET_INVITED,
    ORG_PENDING_INVITE,
    FeedStatus,
)
from transit_odp.organisation.models import DatasetRevision, Organisation
from transit_odp.site_admin.forms import (
    LETTER_CHOICES,
    AgentOrganisationFilterForm,
    AVLSearchFilterForm,
    ConsumerFilterForm,
    OperatorFilterForm,
    TimetableSearchFilterForm,
)

User = get_user_model()


class OrganisationFilter(filters.FilterSet):
    class Meta:
        model = Organisation
        fields = ["status"]
        form = OperatorFilterForm

    STATUS_CHOICES = (
        (ORG_ACTIVE, ORG_ACTIVE),
        (ORG_INACTIVE, ORG_INACTIVE),
        (ORG_PENDING_INVITE, ORG_PENDING_INVITE),
        (ORG_NOT_YET_INVITED, ORG_NOT_YET_INVITED),
    )
    status = filters.ChoiceFilter(
        label="Status",
        empty_label="All statuses",
        choices=STATUS_CHOICES,
    )
    # Needs to be letters to match up with the django form.
    # To aid code reuse the filter forms pass "letters=" back as query params
    letters = filters.MultipleChoiceFilter(
        choices=LETTER_CHOICES,
        lookup_expr="istartswith",
        field_name="name",
    )

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form


class ConsumerFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = ["email"]
        form = ConsumerFilterForm

    letters = filters.MultipleChoiceFilter(
        choices=LETTER_CHOICES,
        lookup_expr="istartswith",
        field_name="email",
    )

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form


class AgentFilter(filters.FilterSet):
    class Meta:
        model = User
        fields = ["agent_organisation"]
        form = AgentOrganisationFilterForm

    letters = filters.MultipleChoiceFilter(
        choices=LETTER_CHOICES,
        lookup_expr="istartswith",
        field_name="agent_organisation",
    )

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form


class BaseDatasetSearchFilter(filters.FilterSet):
    status = filters.ChoiceFilter(
        choices=DatasetRevision.STATUS_CHOICES + ((FeedStatus.live.value, "Published"),)
    )

    def get_form_class(self):
        # bug in base class expects to find form at self._form but it is unset
        return self._meta.form


class TimetableSearchFilter(BaseDatasetSearchFilter):
    class Meta:
        form = TimetableSearchFilterForm
        fields = ["status"]


class AVLSearchFilter(BaseDatasetSearchFilter):
    class Meta:
        form = AVLSearchFilterForm
        fields = ["status"]
