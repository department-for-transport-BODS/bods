from crispy_forms import layout
from crispy_forms.utils import TEMPLATE_PACK
from django.template import Template
from django.template.loader import render_to_string


class TableCell(layout.Div):
    """
    Layout object. It wraps fields in a <tag>
    """

    tag: str = None
    template = "demo/forms/table_cell.html"

    def render(self, form, form_style, context, template_pack=TEMPLATE_PACK, **kwargs):
        # replace form in context with form being render so templated attributes use correct form
        # i.e. when rendering the `empty_form`: Template('id_{{ form.prefix }}').render(context) resolves to 'id_form'
        # not 'id_form-__prefix__'.
        original_form = context.get("form", None)
        context["form"] = form

        fields = self.get_rendered_fields(
            form, form_style, context, template_pack, **kwargs
        )

        if self.css_id is not None:
            self.css_id = Template(self.css_id).render(context)

        # put original form back in context just in case its required for some other reason
        context["form"] = original_form

        template = self.get_template_name(template_pack)
        return render_to_string(
            template, {"elem": self, "tag": self.tag, "fields": fields}
        )


class TR(TableCell):
    tag = "tr"


class TD(TableCell):
    tag = "td"
