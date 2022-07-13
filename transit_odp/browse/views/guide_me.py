from transit_odp.common.views import GuideMeBaseView, Section


class BrowseGuideMeView(GuideMeBaseView):
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
