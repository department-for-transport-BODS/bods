from allauth.account.views import PasswordChangeView as PasswordChangeViewBase
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import HttpResponseRedirect, render
from django.views import View
from django.views.generic import RedirectView
from django.views.generic.base import ContextMixin
from django_hosts.resolvers import reverse
from django_tables2 import SingleTableView
from rest_framework.authtoken.models import Token

from transit_odp.browse.tables import DatasetSubscriptionTable
from transit_odp.browse.views.base_views import BaseTemplateView
from transit_odp.common.view_mixins import BODSBaseView
from transit_odp.organisation.models import Dataset
from transit_odp.publish.views.base import BaseUpdateView
from transit_odp.users.forms.account import PublishAdminNotifications
from transit_odp.users.models import AccountType, UserSettings


class UserRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect view that is used to redirect user after loggin.
    See settings.LOGIN_REDIRECT_URL"""

    permanent = False

    def get_redirect_url(self):
        url = reverse("home", host=self.request.host.name)
        args = self.request.META.get("QUERY_STRING", "")
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        return url


class MyAccountView(BODSBaseView, ContextMixin, View):
    """
    This view shows the user's account page when they are logged in else it shows
    the 'gatekeeper' page
    """

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if not request.user.is_authenticated:
            return render(request, "account/gatekeeper.html", context)
        return render(request, "users/user_account.html", context)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data()
        if self.request.user.is_authenticated:
            kwargs.update({"user": self.request.user})
        return kwargs


class SettingsView(LoginRequiredMixin, BaseUpdateView):
    template_name = "users/users_settings.html"
    model = UserSettings
    form_class = PublishAdminNotifications

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"api_key": Token.objects.get_or_create(user=self.request.user)[0]}
        )
        if self.request.user.account_type == AccountType.developer.value:
            # for developers the notification form doesnt get rendered
            # in the HTML. Take it out of context just to be safe
            context.pop("form")
        return context

    def get_object(self, queryset=None):
        return self.get_queryset().get(user=self.request.user)

    def get_success_url(self):
        # redirect back to same page when finished
        return self.request.path_info


class PasswordChangeView(BODSBaseView, LoginRequiredMixin, PasswordChangeViewBase):
    def get_success_url(self):
        return reverse("account_change_password_done", host=self.request.host.name)


class PasswordChangeDoneView(LoginRequiredMixin, BaseTemplateView):
    template_name = "account/password_change_done.html"


class EmailView(LoginRequiredMixin, RedirectView):
    # TODO - should users be able to update the emails associated with their accounts?
    def get_redirect_url(self, *args, **kwargs):
        # Prohibit access to this view - redirect back to settings
        url = reverse("users:settings", host=self.request.host.name)

        args = self.request.META.get("QUERY_STRING", "")
        if args and self.query_string:
            url = "%s?%s" % (url, args)
        return url


class DatasetManageView(LoginRequiredMixin, SingleTableView):
    template_name = "users/feeds_manage.html"
    model = Dataset
    table_class = DatasetSubscriptionTable
    related_model = None
    related_object = None
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        return super().get_queryset().filter(subscribers=user).add_live_data()

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context.update(
            {"mute_notifications": user.settings.mute_all_dataset_notifications}
        )
        return context

    def post(self, request, *args, **kwargs):
        user = request.user

        mute_notifications = request.POST.get("mute_notifications", False)
        user.settings.mute_all_dataset_notifications = mute_notifications
        user.settings.save()

        return HttpResponseRedirect(request.path_info)
