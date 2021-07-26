from django.shortcuts import render
from django.views.generic import TemplateView

from transit_odp.common.utils.cookie_settings import delete_cookie, set_cookie


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
        is_confirm = "True"

        if (
            "cookie_policy" in request.COOKIES
            and not self.request.GET.get("cookie-accept", None) == "True"
        ):
            is_confirm = "False"

        elif self.request.GET.get("cookie-accept", None) == "False":
            is_confirm = "False"

        context.update({"is_accept": is_confirm})

        response = render(request, self.template_name, context=context)

        if is_confirm == "False" and "cookie_policy" not in request.COOKIES.keys():
            set_cookie(response, key="cookie_policy", value="1", days_expire=None)

        elif is_confirm == "True" and "cookie_policy" in request.COOKIES.keys():
            delete_cookie(response, "cookie_policy")

        return response


class CookieDetailView(TemplateView):
    template_name = "common/cookie_details.html"


class PrivacyPolicyView(TemplateView):
    template_name = "common/privacy.html"
