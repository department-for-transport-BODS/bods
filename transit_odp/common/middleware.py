from django.utils.deprecation import MiddlewareMixin

from transit_odp.common.utils import remove_query_string_param
from transit_odp.site_admin.models import CHAR_LEN, APIRequest


class DefaultHostMiddleware:
    """Updates settings.DEFAULT_HOST to that of incoming request.

    This ensures reverse url is relative to current host by default. This means
    templates that use the url templatetag without supplying hosts argument, e.g.
    library code such as the admin interface, will default to reversing the url
    relative to the request host.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        from django.conf import settings

        current_default = settings.DEFAULT_HOST

        try:
            settings.DEFAULT_HOST = request.host.name
            return self.get_response(request)
        finally:
            settings.DEFAULT_HOST = current_default


class APILoggerMiddleware:
    """Logs any incoming requests to the BODS API in the APIRequest model."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if not request.user.is_authenticated:
            return response

        if request.path.startswith("/api/v1/"):
            user = request.user
            request_meta = request.META
            path_info = request_meta.get("PATH_INFO", "")
            query_string = request_meta.get("QUERY_STRING", "")
            query_string = remove_query_string_param(query_string, "api_key")

            # Truncate string to CHAR_LEN
            path_info = path_info[:CHAR_LEN]
            query_string = query_string[:CHAR_LEN]

            APIRequest.objects.create(
                requestor=user, path_info=path_info, query_string=query_string
            )

        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware for adding security-related HTTP headers to responses.

    This middleware sets various HTTP security headers to enhance the security of
    the application by controlling how resources are loaded and interacted with.

    Headers added by this middleware:
    - Clear-Site-Data: Instructs the browser to clear storage, and execution contexts
      when the response is received and user is anonymous.
    - Permissions-Policy: Controls the permissions for accessing sensitive features
      such as geolocation, microphone, and camera, restricting them to the same origin.
    """

    def process_response(self, request, response):
        """
        Processes the outgoing response before it is sent to the client.
        """
        response[
            "Permissions-Policy"
        ] = "geolocation=(self), microphone=(self), camera=(self)"
        return response
