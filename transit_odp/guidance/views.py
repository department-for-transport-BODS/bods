from collections import namedtuple

import config
from django.views.generic import TemplateView
from django_hosts import reverse

from transit_odp.common.view_mixins import BODSBaseView

Section = namedtuple("Section", "name,title,template")


class SectionedTemplateView(TemplateView):
    """A base view for creating sectioned views. Sectioned views are views that
    change the content of a view based on a section query parameter. You need to
    inherit from this class an add three class attributes.

    Example:
        class MySectionView(SectionedTemplateView):
            template_location = "path/to/template"
            template_name = "template_name/example.html"
            SECTIONS = (Section("section_name", "Section Title",
                        "section_template.html"),)
    """

    def get_section_index_by_name(self, name):
        """Searches SECTIONS for a section by it's name, returning the index of the
        section if found or -1 otherwise.

        Args:
            name (str): The name of the section.

        Returns:
            The index of where the section occurs or -1 if not found.
        """
        index = -1
        found = [
            ind for ind, section in enumerate(self.SECTIONS) if section.name == name
        ]
        if found:
            index = found[0]
        return index

    def get_section_by_name_or_first_section(self, name):
        """Returns the section with name, or the first section.
        Args:
            name (str): the name of the section to find.

        Returns:
            The section with name or the first section.
        """
        section_index = self.get_section_index_by_name(name)
        if section_index > -1:
            return self.SECTIONS[section_index]
        return self.SECTIONS[0]

    def get_next_section(self, name):
        """Gets the section after the section with name name or returns
        None if the section is the last section.

        Args:
            name (str): The name of the current section.

        Returns:
            The next section or None.
        """
        current_section_index = self.get_section_index_by_name(name)
        if current_section_index < len(self.SECTIONS) - 1:
            return self.SECTIONS[current_section_index + 1]
        else:
            return None

    def get_prev_section(self, name):
        """Gets the section before the section with name name, if the
        section is the first section it returns None.

        Args:
            name (str): The name of the current section.

        Returns:
            The previous section or None.
        """
        current_section_index = self.get_section_index_by_name(name)
        if current_section_index == 0:
            return None
        else:
            return self.SECTIONS[current_section_index - 1]

    def get_template_by_section_name(self, name):
        """Returns a section template from it's name, if the name doesn't exist
        then the template of the first template is returned."""
        section = self.SECTIONS[0]
        index = self.get_section_index_by_name(name)
        if index > -1:
            section = self.SECTIONS[index]

        template = f"{self.template_location}/{section.template}"
        return template

    def get_template_names(self):
        section_name = self.request.GET.get("section", self.SECTIONS[0].name)
        return self.get_template_by_section_name(section_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section_name = self.request.GET.get("section", self.SECTIONS[0].name)
        context["sections"] = self.SECTIONS

        current_section = self.get_section_by_name_or_first_section(section_name)
        context["current_section"] = current_section
        context["next_section"] = self.get_next_section(current_section.name)
        context["prev_section"] = self.get_prev_section(current_section.name)
        return context


# Developer Guidance
class DeveloperGuidanceHomeView(BODSBaseView, TemplateView):
    template_name = "guidance/guidance_developers.html"


class DeveloperReqView(BODSBaseView, SectionedTemplateView):
    template_location = "guidance/developer"
    template_name = f"{template_location}/base.html"
    SECTIONS = (
        Section("overview", "Overview", "overview.html"),
        Section("quickstart", "Quick start", "quick_start.html"),
        Section(
            "databyoperator", "Data by operator or location", "data_by_op_loc.html"
        ),
        Section("browse", "Browse for specific data", "browse_data.html"),
        Section("download", "Downloading data", "downloading_data.html"),
        Section("api", "Using the APIs", "using_the_api.html"),
        Section("apireference", "API reference", "api_reference.html"),
        Section("dataformats", "Data formats", "data_formats.html"),
        Section("help", "How to get help", "help.html"),
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["api_base"] = reverse("api:api-root", host=config.hosts.DATA_HOST)
        return context


# Publisher Guidance


class SupportOperatorHomeView(BODSBaseView, TemplateView):
    template_name = "guidance/guidance_operators.html"


class LocalAuthorityReqView(BODSBaseView, SectionedTemplateView):
    template_location = "guidance/local_authorities"
    template_name = f"{template_location}/base.html"
    SECTIONS = (
        Section("overview", "Overview", "overview.html"),
        Section("support", "Supporting operators", "support.html"),
        Section("agent", "Being an Agent", "agent.html"),
        Section("naptan", "NaPTAN stop data", "naptan.html"),
        Section(
            "local-auth-buses",
            "Providing data for Local Authority operated buses",
            "local_authority_buses.html",
        ),
        Section("usingbods", "Using Bus Open Data", "use_open_data.html"),
        Section("help", "How to get help", "help.html"),
    )


class BusOperatorReqView(BODSBaseView, SectionedTemplateView):
    template_location = "guidance/bus_operators"
    template_name = f"{template_location}/base.html"
    # TODO SECTIONS should ensure section.name is unique
    SECTIONS = (
        Section("overview", "Overview", "overview.html"),
        Section("whopublishes", "Who must publish open data?", "who_publish_data.html"),
        Section("registering", "Using our account", "register_bus_open_data.html"),
        Section("agents", "Agents", "agents.html"),
        Section("publishing", "Publishing data", "publish_data.html"),
        Section("descriptions", "Writing data descriptions", "descriptions.html"),
        Section("timetables", "Timetables data", "timetables.html"),
        Section("buslocation", "Bus location data", "buslocation.html"),
        Section("fares", "Fares data", "fares.html"),
        Section("dataquality", "Data quality", "dataquality.html"),
        Section("help", "How to get help", "help.html"),
    )
