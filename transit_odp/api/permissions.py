from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsReadOnlyUser(IsAuthenticated):
    """
    Editable for organisation users and read only for authenticated non-organisation
    users.
    """

    def has_permission(self, request, view):
        is_auth = super().has_permission(request, view)
        if request.method in SAFE_METHODS:
            return is_auth
        return is_auth and request.user.is_org_user
