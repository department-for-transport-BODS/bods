from django.contrib import admin

from transit_odp.data_quality.models import DataQualityReport, StopPoint
from transit_odp.data_quality.scoring import DataQualityCounts


@admin.register(DataQualityReport)
class DataQualityReportAdmin(admin.ModelAdmin):
    readonly_fields = ("revision", "data_quality_input_counts")
    fields = ("revision", "data_quality_input_counts")

    def data_quality_input_counts(self, obj):
        return DataQualityCounts.from_report_id(obj.id)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(StopPoint)
class DataQualityStopPointAdmin(admin.ModelAdmin):
    search_fields = ("atco_code", "ito_id")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
