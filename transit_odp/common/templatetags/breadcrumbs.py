from django import template
from django.template import Node, Variable, VariableDoesNotExist
from django.utils.encoding import smart_text
from django.utils.html import escape
from django.utils.translation import gettext as _
from django_hosts.templatetags.hosts import host_url

register = template.Library()


@register.tag
def breadcrumb(parser, token):
    """
    Renders the breadcrumb.
    Examples:
        {% breadcrumb "Title of breadcrumb" url_var %}
        {% breadcrumb context_var  url_var %}
        {% breadcrumb "Just the title" %}
        {% breadcrumb just_context_var %}

    Parameters:
    -First parameter is the title of the crumb,
    -Second (optional) parameter is the url variable to link to,
        produced by url tag, i.e.:
        {% url person_detail object.id as person_url %}
        then:
        {% breadcrumb person.name person_url %}

    @author Andriy Drozdyuk
    """
    try:
        tag_name, title, *optional_url = token.split_contents()
        url = optional_url[0] if optional_url else None
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires at least one argument" % token.contents.split()[0]
        )

    return BreadcrumbNode(title, url)


@register.tag
def breadcrumb_url(parser, token):
    """
    Same as breadcrumb
    but instead of url context variable takes in all the
    arguments URL tag takes.
        {% breadcrumb "Title of breadcrumb" person_detail person.id %}
        {% breadcrumb person.name person_detail person.id %}
    """

    bits = token.split_contents()
    if len(bits) == 2:
        return breadcrumb(parser, token)

    # Extract our extra title parameter
    title = bits.pop(1)
    token.contents = " ".join(bits)

    url_node = host_url(parser, token)

    return UrlBreadcrumbNode(title, url_node)


class BreadcrumbNode(Node):
    def __init__(self, title, url=None):
        """
        First var is title, second var is url context variable
        """
        self.title = Variable(title)
        self.url = Variable(url) if url else None

    def render(self, context):
        title = self.title.var

        if title.find("'") == -1 and title.find('"') == -1:
            try:
                title = self.title.resolve(context)
            except Exception:
                title = ""

        else:
            title = title.strip("'").strip('"')
            title = smart_text(title)

        url = None

        if self.url:
            try:
                url = self.url.resolve(context)
            except VariableDoesNotExist:
                print("URL does not exist", self.url)
                url = None

        return create_crumb(title, url)


class UrlBreadcrumbNode(Node):
    def __init__(self, title, url_node):
        self.title = Variable(title)
        self.url_node = url_node

    def render(self, context):
        title = self.title.var

        if title.find("'") == -1 and title.find('"') == -1:
            try:
                val = self.title
                title = val.resolve(context)
            except Exception:
                title = ""
        else:
            title = title.strip("'").strip('"')
            title = smart_text(title)

        url = self.url_node.render(context)
        return create_crumb(title, url)


def create_crumb(title, url=None):
    """
    Helper function
    """
    title = _(escape(title))
    link = (
        f'<a class="govuk-breadcrumbs__link" href="{url}">{title}</a>' if url else title
    )
    crumb = f'<li class="govuk-breadcrumbs__list-item">{link}</li>'
    return crumb
