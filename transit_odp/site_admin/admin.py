from django.contrib import admin

from transit_odp.site_admin.models import (
    APIRequest,
    OperationalStats,
    ResourceRequestCounter,
)

admin.site.register(OperationalStats)


@admin.register(APIRequest)
class APIRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_precise",
        "path_info",
        "query_string",
        "requestor_id",
    )

    readonly_fields = ("id", "created", "path_info", "query_string", "requestor_id")

    @admin.display(description="Created")
    def created_precise(self, obj):
        return obj.created.strftime("%d %b %Y %H:%M:%S")

    def get_ordering(self, request):
        return ()

    def get_sortable_by(self, request):
        return ()

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def has_change_permission(self, request, instance=None):
        return False


@admin.register(ResourceRequestCounter)
class ResourceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "date",
        "path_info",
        "counter",
        "requestor_id",
    )

    readonly_fields = (
        "id",
        "date",
        "path_info",
        "counter",
        "requestor_id",
    )

    def get_ordering(self, request):
        return ()

    def get_sortable_by(self, request):
        return ()

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def has_change_permission(self, request, instance=None):
        return False
