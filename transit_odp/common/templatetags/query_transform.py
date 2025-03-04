from django import template

register = template.Library()


# See https://gist.github.com/benbacardi/d6cd0fb8c85e1547c3c60f95f5b2d5e1
@register.simple_tag(takes_context=True)
def query_transform(context, **kwargs):
    """
    Returns the URL-encoded querystring for the current page,
    updating the params with the key/value pairs passed to the tag.

    E.g: given the querystring ?foo=1&bar=2
    {% query_transform bar=3 %} outputs ?foo=1&bar=3
    {% query_transform foo='baz' %} outputs ?foo=baz&bar=2
    {% query_transform foo='one' bar='two' baz=99 %} outputs ?foo=one&bar=two&baz=99

    A RequestContext is required for access to the current querystring.
    """
    query = context["request"].GET.copy()
    for k, v in kwargs.items():
        query[k] = v
    return "?" + query.urlencode()


@register.simple_tag(takes_context=True)
def query_transform_kv(context, key, value):
    """
    Returns the URL-encoded querystring for the current page,
    updating the params with the key/value pair passed to the tag.

    E.g: given the querystring ?foo=1&bar=2
    {% query_transform 'bar' 3 %} outputs ?foo=1&bar=3
    {% query_transform param 'baz' %} outputs ?foo=1&bar=baz (where param='bar' passed from template)

    A RequestContext is required for access to the current querystring.
    """
    query = context["request"].GET.copy()
    query[key] = value
    return "?" + query.urlencode()


@register.simple_tag(takes_context=True)
def query_chop(context, key_to_chop):
    """
    Returns the URL-encoded querystring for the current page,
    removing the querystring param in the arg.

    E.g: given the querystring ?foo=1&bar=2
    {% query_chop bar %} outputs ?foo=1

    """
    query = context["request"].GET.copy()
    # popout submitform if its there
    query.pop("submitform", None)
    if key_to_chop in query:
        del query[key_to_chop]
    return "?" + query.urlencode()


@register.simple_tag(takes_context=True)
def remove_query_params(context):
    """
    Returns the URL for the current page,
    after removing the query params.

    E.g: given the url is https://localhost/view?page=1&details=2
    {% remove_query_params %} outputs https://localhost/view

    """

    url = context["request"].build_absolute_uri()
    url = url.split("?")[0]
    return url
