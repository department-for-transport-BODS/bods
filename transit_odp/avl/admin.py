from django.contrib import admin

from .models import AVLSchemaValidationReport, AVLValidationReport


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
