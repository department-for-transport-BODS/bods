from django.contrib import admin

from ..models import AVLSchemaValidationReport, AVLValidationReport
from ..proxies import AVLDataset
from .forms import DummyDatafeedForm


@admin.register(AVLValidationReport)
class AVLValidationReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "dataset_id",
        "revision_id",
        "critical_count",
        "critical_score",
        "non_critical_count",
        "non_critical_score",
        "vehicle_activity_count",
    )
    search_fields = ("revision__dataset__id",)

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related("revision")

    def dataset_id(self, instance):
        return instance.revision.dataset_id


@admin.register(AVLSchemaValidationReport)
class AVLSchemaValidationReportAdmin(admin.ModelAdmin):
    list_display = ("id", "created", "dataset_id", "error_count")
    search_fields = ("revision__dataset__id",)

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related("revision")

    def dataset_id(self, instance):
        return instance.revision.dataset_id


@admin.register(AVLDataset)
class DummyDatafeedAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "username", "created")
    list_display_links = ("name",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .filter(is_dummy=True)
            .select_related("live_revision")
        )

    def get_form(self, request, obj=None, change=False, **kwargs):
        return DummyDatafeedForm

    def name(self, obj):
        return obj.live_revision.name

    def username(self, obj):
        return obj.live_revision.username

    def url(self, obj):
        return obj.live_revision.url_link

    def get_deleted_objects(self, objs, request):
        # We dont normally allow the deleting of revisions in the django admin
        # but this is the live revision of the dummy dataset so its fine
        to_delete, model_count, perms_needed, protected = super().get_deleted_objects(
            objs, request
        )
        return to_delete, model_count, set(), protected
