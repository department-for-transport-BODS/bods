from collections import namedtuple

from django.views.generic import TemplateView

from transit_odp.common.view_mixins import BODSBaseView

Section = namedtuple("Section", ["title", "template"])


class GuideMeView(BODSBaseView, TemplateView):
    template_location = "browse/guideme"
    template_name = f"{template_location}/guide_me.html"

    SECTIONS = (
        Section(
            "Read supporting documents",
            f"{template_location}/read_supporting_documents.html",
        ),
        Section(
            "See what is on BODS",
            f"{template_location}/see_what_in_on_bods.html",
        ),
        Section(
            "Get an account",
            f"{template_location}/get_an_account.html",
        ),
        Section(
            "Use download",
            f"{template_location}/use_download.html",
        ),
        Section(
            "Use API",
            f"{template_location}/use_api.html",
        ),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = self.SECTIONS
        return context
