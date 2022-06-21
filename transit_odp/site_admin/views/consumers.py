from django.contrib.auth import get_user_model
from django.db.models.functions.text import Substr, Upper
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, UpdateView
from django_filters.views import FilterView
from django_hosts import reverse
from django_tables2.views import SingleTableView
from invitations.utils import get_invitation_model

from config.hosts import ADMIN_HOST
from transit_odp.common.forms import ConfirmCancelForm
from transit_odp.site_admin.filters import ConsumerFilter
from transit_odp.site_admin.forms import EditNotesForm
from transit_odp.site_admin.tables import ConsumerTable
from transit_odp.users.constants import DeveloperType
from transit_odp.users.views.mixins import SiteAdminViewMixin

Invitation = get_invitation_model()
User = get_user_model()

__all__ = [
    "ConsumerDetailView",
    "ConsumerListView",
    "RevokeConsumerSuccessView",
    "RevokeConsumerView",
    "UpdateConsumerNotesView",
]


class ConsumerDetailView(SiteAdminViewMixin, DetailView):
    template_name = "site_admin/consumers/detail.html"
    model = User

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(account_type=DeveloperType)


class ConsumerListView(SiteAdminViewMixin, FilterView, SingleTableView):
    model = User
    template_name = "site_admin/consumers/list.html"
    table_class = ConsumerTable
    filterset_class = ConsumerFilter
    paginate_by = 25

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .annotate(email_first_letter=Upper(Substr("email", 1, 1)))
            .filter(account_type=DeveloperType)
            .order_by("email")
        )
        search_term = self.request.GET.get("q", "").strip()
        if search_term:
            qs = qs.filter(email__istartswith=search_term)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "").strip()
        context["letters"] = self.request.GET.getlist("letters")
        return context


class RevokeConsumerSuccessView(SiteAdminViewMixin, DetailView):
    model = User
    template_name = "site_admin/consumers/revoke_success.html"

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(account_type=DeveloperType)


class RevokeConsumerView(SiteAdminViewMixin, UpdateView):
    """A view to update whether a developer account is active or inactive."""

    model = User
    form_class = ConfirmCancelForm
    template_name = "site_admin/consumers/revoke.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        return kwargs

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(account_type=DeveloperType)

    def form_valid(self, form):
        user = self.get_object()
        submit = form.data.get("submit")

        if submit == "confirm":
            url_name = "users:revoke-consumer-success"
            user.is_active = False
            user.save()
        else:
            url_name = "users:consumer-detail"

        kwargs = {"pk": self.get_object().id}
        url = reverse(
            url_name,
            kwargs=kwargs,
            host=ADMIN_HOST,
        )

        return HttpResponseRedirect(url)


class UpdateConsumerNotesView(SiteAdminViewMixin, UpdateView):
    model = User
    template_name = "site_admin/consumers/edit_notes.html"
    form_class = EditNotesForm

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(account_type=DeveloperType)

    def get_success_url(self):
        user = self.get_object()
        view_name = "users:consumer-detail"
        url = reverse(view_name, kwargs={"pk": user.id}, host=ADMIN_HOST)
        return url
