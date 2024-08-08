# Code copied from https://gist.github.com/fleepgeek/92b01d3187cf92b4495d71c69ee818df
from django.contrib.sessions.models import Session

from transit_odp.restrict_sessions.models import LoggedInUser


class OneSessionPerUserMiddleware:
    # Called only once when the web server starts
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        if request.user.is_authenticated:
            current_session_key = request.session.session_key

            try:
                logged_in_user = LoggedInUser.objects.get(user=request.user)
                stored_session_key = logged_in_user.session_key
                # if there is a stored_session_key  in our database and it is
                # different from the current session, delete the stored_session_key
                # session_key with from the Session table

                if stored_session_key != current_session_key:
                    # Update session key for the user
                    request.user.logged_in_user.session_key = current_session_key
                    request.user.logged_in_user.save()

                    # Delete the old session if it exists
                    if stored_session_key:
                        Session.objects.filter(session_key=stored_session_key).delete()

            except LoggedInUser.DoesNotExist:
                # Create a new LoggedInUser entry if it does not exist
                LoggedInUser.objects.create(
                    user=request.user, session_key=current_session_key
                )

        response = self.get_response(request)

        # This is where you add any extra code to be executed for each
        # request/response after the view is called.
        # For this tutorial, we're not adding any code so we just return the response
        return response
