"""
Buttons
=======

.. _DS: https://design-system.service.gov.uk/

References
    * `Button <https://design-system.service.gov.uk/components/button/>`_;

"""  # noqa: E501
from typing import Optional

from crispy_forms.layout import TemplateNameMixin
from crispy_forms.utils import TEMPLATE_PACK, flatatt
from django.template import Template
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

__all__ = ["BaseInput", "ButtonElement", "ButtonSubmit", "LinkButton"]


def render_template(context, value):
    return Template(value).render(context)


class BaseNode(TemplateNameMixin):
    @classmethod
    def render_template(cls, context, value):
        return render_template(context, value)


class BaseInput(BaseNode):
    """
    A base class to reduce the amount of code in the Input classes.
    """

    template = "%s/layout/baseinput.html"

    def __init__(self, name, value, **kwargs):
        self.name = name
        self.value = value
        self.id = kwargs.pop("css_id", "")

        self.attrs = {}

        if "css_class" in kwargs:
            self.field_classes += " %s" % kwargs.pop("css_class")

        self.template = kwargs.pop("template", self.template)
        self.flat_attrs = flatatt(kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        """
        Renders an `<input />` if container is used as a Layout object.
        Input button value can be a variable in context.
        """
        if self.value is not None:
            self.value = self.render_template(context, self.value)

        context.update({"input": self})

        template = self.get_template_name(template_pack)
        return render_to_string(template, context.flatten())


class ButtonElement(BaseInput):
    """Creates a ``<button type="button">`` element.

    Contrary to ``Button``, ButtonElement uses a ``<button>`` element rather than an
    ``<input>``. The button's type is set to "button" to create a clickable button -
    useful to add JavaScript functionality.

    Example:
        .. code-block:: python

            button = ButtonElement('name', 'value', content="Copy")

    Notes:
        * First argument is for ``name`` attribute and also turned into the id for the \
         button;
        * Second argument is for ``value`` attribute and also for element content if \
        not given;
        * Third argument is an optional named argument ``content``, if given it \
        will be appended inside element instead of ``value``. Content string is \
        marked as safe so you can put anything you want;
    """

    template = "%s/layout/basebutton.html"
    input_type = "button"
    field_classes = "govuk-button"

    def __init__(
        self,
        name: Optional[str] = None,
        value: Optional[str] = None,
        onclick: Optional[str] = None,
        content: Optional[str] = None,
        *args,
        **kwargs
    ):
        self.onclick = onclick
        self.content = content
        super().__init__(name, value, **kwargs)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        """Renders `template` using context.

        Notes:     * Assigns `button_content=content` to `context`
        """
        if self.onclick is not None:
            self.onclick = self.render_template(context, self.onclick)

        if self.content is not None:
            self.content = self.render_template(context, self.content)

        return super().render(form, form_style, context, template_pack)


class ButtonSubmit(ButtonElement):
    """Creates a ``<button type="submit">`` element.

    Example:
         .. code-block:: python

            button = ButtonSubmit('save', 'save',
                                    content="Save and continue")
    """

    input_type = "submit"

    def __init__(
        self,
        name: Optional[str] = None,
        value: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs
    ):
        if content is None:
            content = _("Confirm")
        super().__init__(name=name, value=value, content=content, **kwargs)


class LinkButton(BaseNode):
    """Create an `<a>` element with the styling of a govuk-button `<button>` element.

    Example:
        .. code-block:: python

            button = CancelLinkButton('/', content="Return to home")
    """

    template: str = "%s/layout/link.html"
    field_classes: str = "govuk-button govuk-button--secondary"
    url: str

    def __init__(self, url: str, content: str = None, **kwargs):
        if content is None:
            content = _("Cancel")

        self.url = url
        self.id = kwargs.pop("css_id", "")
        self.content = content

        if "css_class" in kwargs:
            self.field_classes += " %s" % kwargs.pop("css_class")

        self.template = kwargs.pop("template", self.template)

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        template = self.get_template_name(template_pack)

        if self.content is not None:
            self.content = self.render_template(context, self.content)

        if self.url is not None:
            self.url = self.render_template(context, self.url)

        context.update({"input": self})

        return render_to_string(template, context.flatten())
