from django.contrib import admin

from .models import AVLValidationReport


@admin.register(AVLValidationReport)
class AVLValidationReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created",
        "dataset_id",
        "revision_id",
        "critical_count",
        "non_critical_count",
    )
    search_fields = ("revision__dataset__id",)

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related("revision")

    def dataset_id(self, instance):
        return instance.revision.dataset_id
