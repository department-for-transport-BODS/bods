from django.dispatch import Signal

# Signal new user has accepted invite and filled in form
# organisations are now set up
user_accepted = Signal(providing_args=["invite", "user"])
