from urllib.parse import quote

from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.template import loader
from django.views.decorators.csrf import requires_csrf_token

from transit_odp.common.utils.flags import Feature


@requires_csrf_token
def page_not_found(request, exception, template_name="404.html"):
    """
    Custom 404 handler. Shamefully copied from django.views.defaults

    Templates: :template:`404.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/'). It's
            quoted to prevent a content injection attack.
        exception
            The message from the exception which triggered the 404 (if one was
            supplied), or the exception class name
    """
    exception_repr = exception.__class__.__name__
    # Try to get an "interesting" exception message, if any (and not the ugly
    # Resolver404 dictionary)
    try:
        message = exception.args[0]
    except (AttributeError, IndexError):
        pass
    else:
        if isinstance(message, str):
            exception_repr = message
    context = {
        "request_path": quote(request.path),
        "exception": exception_repr,
        "feature": Feature(),
    }
    template = loader.get_template(template_name)
    body = template.render(context, request)
    content_type = None  # Django will use DEFAULT_CONTENT_TYPE

    return HttpResponseNotFound(body, content_type=content_type)


@requires_csrf_token
def permission_denied(request, exception, template_name="403.html"):
    """
    Custom 403 handler.

    Templates: :template:`403.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/'). It's
            quoted to prevent a content injection attack.
        exception
            The message from the exception which triggered the 404 (if one was
            supplied), or the exception class name
    """
    exception_repr = exception.__class__.__name__
    try:
        message = exception.args[0]
    except (AttributeError, IndexError):
        pass
    else:
        if isinstance(message, str):
            exception_repr = message
    context = {
        "request_path": quote(request.path),
        "exception": exception_repr,
        "feature": Feature(),
    }
    template = loader.get_template(template_name)
    body = template.render(context, request)
    content_type = None  # Django will use DEFAULT_CONTENT_TYPE

    return HttpResponseForbidden(body, content_type=content_type)
