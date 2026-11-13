from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from transit_odp.users.forms.admin import UserChangeForm, UserCreationForm

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):
    # Note - to add extra  below to add extra fields, e.g. 'account_type'
    form = UserChangeForm
    add_form = UserCreationForm

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "email",
                    "password",
                    "account_type",
                    "organisations",
                    "username",
                    "dev_organisation",
                    "agent_organisation",
                    "description",
                    "opt_in_user_research",
                    "share_app_usage",
                )
            },
        ),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "password1",
                    "password2",
                    "account_type",
                    "username",
                    "dev_organisation",
                    "agent_organisation",
                    "description",
                    "opt_in_user_research",
                    "share_app_usage",
                ),
            },
        ),
    )
    list_display = [
        "username",
        "email",
        "is_superuser",
        "account_type",
    ]

    list_filter = auth_admin.UserAdmin.list_filter + ("account_type",)
    search_fields = ["username", "first_name", "last_name", "email"]

    def opt_in_user_research(self, obj):
        if obj.organisation is None:
            return None
        return obj.opt_in_user_research

    opt_in_user_research.short_description = "opt_in_user_research"

    def share_app_usage(self, obj):
        if obj.organisation is None:
            return None
        return obj.share_app_usage

    share_app_usage.short_description = "share_app_usage"
