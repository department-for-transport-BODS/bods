from django.conf import settings
from django.urls import include, path
from django_axe import urls

from transit_odp.organisation.views import (
    InviteSuccessView,
    InviteView,
    ManageView,
    OrgProfileEditSuccessView,
    OrgProfileEditView,
    OrgProfileView,
    ResendAgentUserInviteSuccessView,
    ResendAgentUserInviteView,
    ResendInviteSuccessView,
    ResendInviteView,
    UserAgentAcceptResponseView,
    UserAgentLeaveOrgSuccessView,
    UserAgentLeaveOrgView,
    UserAgentRejectResponseView,
    UserAgentRemoveSuccessView,
    UserAgentRemoveView,
    UserAgentResponseView,
    UserArchiveView,
    UserDetailView,
    UserEditSuccessView,
    UserEditView,
    UserIsActiveView,
)
from transit_odp.users.views.account import (
    MyAccountView,
    SettingsView,
    UserRedirectView,
)

AGENT_PATHS = [
    path(
        "leave/<int:pk>/",
        view=UserAgentLeaveOrgView.as_view(),
        name="agent-user-leave",
    ),
    path(
        "leave/<int:pk>/success/",
        view=UserAgentLeaveOrgSuccessView.as_view(),
        name="agent-user-leave-success",
    ),
    path(
        "invite/<int:pk>/",
        view=UserAgentResponseView.as_view(),
        name="agent-user-response",
    ),
    path(
        "invite/<int:pk>/accepted/",
        view=UserAgentAcceptResponseView.as_view(),
        name="agent-user-response-accepted",
    ),
    path(
        "invite/<int:pk>/rejected/",
        view=UserAgentRejectResponseView.as_view(),
        name="agent-user-response-rejected",
    ),
    path(
        "invite/<int:pk>/resend/",
        view=ResendAgentUserInviteView.as_view(),
        name="agent-resend-invite",
    ),
    path(
        "invite/<int:pk>/resend/success/",
        view=ResendAgentUserInviteSuccessView.as_view(),
        name="agent-resend-invite-success",
    ),
    path(
        "remove/<int:pk>/",
        view=UserAgentRemoveView.as_view(),
        name="agent-remove",
    ),
    path(
        "remove/<int:pk>/success/",
        view=UserAgentRemoveSuccessView.as_view(),
        name="agent-remove-success",
    ),
]

app_name = "users"
urlpatterns = [
    path("", view=MyAccountView.as_view(), name="home"),
    path("settings/", view=SettingsView.as_view(), name="settings"),
    path("agent/", include(AGENT_PATHS)),
    path(
        "manage/",
        include(
            [
                path("<int:pk>/", view=ManageView.as_view(), name="manage"),
                path("invite/", view=InviteView.as_view(), name="invite"),
                path(
                    "invite/success/",
                    view=InviteSuccessView.as_view(),
                    name="invite-success",
                ),
                path(
                    "org-profile/<int:pk>/",
                    include(
                        [
                            path(
                                "",
                                view=OrgProfileView.as_view(),
                                name="organisation-profile",
                            ),
                            path(
                                "edit",
                                view=OrgProfileEditView.as_view(),
                                name="edit-org-profile",
                            ),
                            path(
                                "edit/success/",
                                view=OrgProfileEditSuccessView.as_view(),
                                name="edit-org-profile-success",
                            ),
                        ]
                    ),
                ),
                path(
                    "<int:pk>/",
                    include(
                        [
                            path(
                                "archive/",
                                view=UserIsActiveView.as_view(),
                                name="archive",
                            ),
                            path(
                                "archive-success/",
                                view=UserArchiveView.as_view(),
                                name="archive-success",
                            ),
                            path(
                                "activate/",
                                view=UserIsActiveView.as_view(),
                                name="activate",
                            ),
                            path(
                                "re-invite/",
                                view=ResendInviteView.as_view(),
                                name="re-invite",
                            ),
                            path(
                                "re-invite/success/",
                                view=ResendInviteSuccessView.as_view(),
                                name="re-invite-success",
                            ),
                            path(
                                "detail/",
                                view=UserDetailView.as_view(),
                                name="manage-user-detail",
                            ),
                            path(
                                "edit/",
                                view=UserEditView.as_view(),
                                name="manage-user-edit",
                            ),
                            path(
                                "edit-success/",
                                view=UserEditSuccessView.as_view(),
                                name="manage-user-edit-success",
                            ),
                        ]
                    ),
                ),
            ]
        ),
    ),
    # Used to redirect back to user's account page
    path("~redirect/", view=UserRedirectView.as_view(), name="redirect"),
]

if "django_axe" in settings.INSTALLED_APPS and settings.DJANGO_AXE_ENABLED:
    urlpatterns = [path("axe/", include(urls, namespace="django_axe"))] + urlpatterns
