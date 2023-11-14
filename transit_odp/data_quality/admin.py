from django.urls import path
from django.contrib import admin
from django.db.models import F
from django.http import FileResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.html import format_html

from transit_odp.data_quality.models import DataQualityReport, StopPoint
from transit_odp.data_quality.scoring import DataQualityCounts


@admin.register(DataQualityReport)
class DataQualityReportAdmin(admin.ModelAdmin):
    list_display = (
        "dataset_id",
        "organisation_name",
        "score",
        "download_link",
        "revision_id",
        "created",
    )
    search_fields = ("dataset_id", "organisation_name")
    readonly_fields = ("revision", "data_quality_input_counts")
    fields = ("revision", "data_quality_input_counts")
    actions = None

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "download-file/<int:pk>",
                self.download_file,
                name="data_quality_report_download-file",
            ),
        ]
        return urls

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .annotate(
                organisation_name=F("revision__dataset__organisation__name"),
                dataset_id=F("revision__dataset_id"),
            )
        )

    @admin.display(
        ordering="dataset_id"
    )
    def dataset_id(self, instance):
        return instance.dataset_id

    @admin.display(
        ordering="organisation_name"
    )
    def organisation_name(self, instance):
        return instance.organisation_name

    @admin.display(
        description="Download file"
    )
    def download_link(self, instance):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:data_quality_report_download-file", args=[instance.pk]),
            instance.file.name,
        )


    def download_file(self, request, pk):
        if request.user.is_anonymous or not request.user.is_superuser:
            return HttpResponseForbidden("not admin user", content_type="text/html")
        report = DataQualityReport.objects.get(pk=pk)
        response = FileResponse(report.file.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={report.file.name}"
        return response


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
