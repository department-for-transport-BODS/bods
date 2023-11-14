from django.contrib import admin

from transit_odp.changelog.models import HighLevelRoadMap
from transit_odp.changelog.proxies import ConsumerKnownIssues, PublisherKnownIssues


@admin.register(ConsumerKnownIssues, PublisherKnownIssues)
class KnownIssueAdmin(admin.ModelAdmin):
    list_display = ["status", "description", "modified", "created", "deleted"]
    list_display_links = ["description"]
    search_fields = ["description"]
    list_filter = ["status", "deleted"]
    exclude = ["category"]
    actions = None

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HighLevelRoadMap)
class HighLevelRoadMapAdmin(admin.ModelAdmin):
    list_display = ["description", "modified", "created"]
    actions = None

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


