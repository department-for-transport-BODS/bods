import logging
from collections import namedtuple
from typing import Any

from django.conf import settings
from django.shortcuts import render
from django.views.generic import DetailView, TemplateView, UpdateView

from transit_odp.common.constants import FALSE, TRUE
from transit_odp.common.utils.cookie_settings import delete_cookie, set_cookie
from transit_odp.common.view_mixins import BODSBaseView

logger = logging.getLogger(__name__)


class ComingSoonView(TemplateView):
    template_name = "common/placeholder.html"


class VersionView(TemplateView):
    template_name = "common/version.html"


class CookieView(TemplateView):
    template_name = "common/main_cookie.html"

    def get_context_data(self, **kwargs):
        display_cookie_confirm = False
        if "cookie-accept" in self.request.GET:
            display_cookie_confirm = True

        kwargs.update({"display_cookie_confirm": display_cookie_confirm})

        return kwargs

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        is_confirm = FALSE

        cookie_policy_value = request.COOKIES.get("cookie_policy", None)

        if (
            cookie_policy_value == "accept"
            and not self.request.GET.get("cookie-accept", None) == FALSE
        ):
            is_confirm = TRUE

        elif self.request.GET.get("cookie-accept", None) == TRUE:
            is_confirm = TRUE

        context.update({"is_accept": is_confirm})

        response = render(request, self.template_name, context=context)

        if "cookie-accept" in request.GET:
            if is_confirm == TRUE:
                set_cookie(response, key="cookie_policy", value="accept", days_expire=None)
            else:
                set_cookie(response, key="cookie_policy", value="reject", days_expire=None)

        return response


class CookieDetailView(TemplateView):
    template_name = "common/cookie_details.html"


class PrivacyPolicyView(TemplateView):
    template_name = "common/privacy.html"


class BaseTemplateView(BODSBaseView, TemplateView):
    pass


class BaseDetailView(BODSBaseView, DetailView):
    pass


class BaseUpdateView(BODSBaseView, UpdateView):
    pass


Section = namedtuple("Section", ["title", "template"])


class GuideMeBaseView(BaseTemplateView):
    SECTIONS = None
    template_name = "common/guide_me.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = self.SECTIONS
        return context


class CoachDownloadView(BaseTemplateView):
    template_name = "common/coach_download.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["txc_file"] = settings.COACH_TXC_FILE_S3_URL
        context["atco_file"] = settings.COACH_ATCO_FILE_S3_URL

        return context
