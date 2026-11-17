from rest_framework.authentication import TokenAuthentication


class TokenAuthSupportQueryString(TokenAuthentication):
    """
    Extend the TokenAuthentication class to support querystring authentication
    in the form of "http://www.example.com/?api_key=<token_key>"
    """

    def authenticate(self, request):
        # Check if API_KEY_PARAM is in the request query params.
        # Give precedence to 'Authorization' header.
        API_KEY_PARAM = "api_key"
        if (
            API_KEY_PARAM in request.query_params
            and "HTTP_AUTHORIZATION" not in request.META
        ):
            return self.authenticate_credentials(
                request.query_params.get(API_KEY_PARAM)
            )
        else:
            return super(TokenAuthSupportQueryString, self).authenticate(request)
