from django.urls import path
from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html

from transit_odp.avl.admin.forms import (
    DummyDatafeedForm,
    PostPublishingCheckReportAdminForm,
)
from transit_odp.avl.models import (
    AVLSchemaValidationReport,
    AVLValidationReport,
    PostPublishingCheckReport,
)
from transit_odp.avl.proxies import AVLDataset


class CustomAdminFileWidget(AdminFileWidget):
    """
    Custom file widget that doesnt display currently link
    """

    template_name = "avl/custom_form_widgets/custom_admin_file_widget.html"


@admin.register(AVLValidationReport)
class AVLValidationReportAdmin(admin.ModelAdmin):
    formfield_overrides = {models.FileField: {"widget": CustomAdminFileWidget}}
    list_display = (
        "dataset_id",
        "organisation_name",
        "download_report",
        "revision_id",
        "critical_count",
        "critical_score",
        "non_critical_count",
        "non_critical_score",
        "vehicle_activity_count",
        "created",
    )
    readonly_fields = ("dataset_id", "organisation_name", "download_report")
    fields = (
        "dataset_id",
        "organisation_name",
        "download_report",
        "file",
        "revision",
        "critical_count",
        "critical_score",
        "non_critical_count",
        "non_critical_score",
        "vehicle_activity_count",
        "created",
    )
    search_fields = ("revision__dataset__id", "revision__dataset__organisation__name")

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "download-avl-validation-report/<int:pk>",
                self.download_validation_report,
                name="avl-validation-report",
            ),
        ]
        return urls

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .select_related("revision", "revision__dataset__organisation")
        )

    @admin.display(ordering="revision__dataset__id")
    def dataset_id(self, instance):
        return instance.revision.dataset_id

    @admin.display(ordering="revision__dataset__organisation__name")
    def organisation_name(self, instance):
        return instance.revision.dataset.organisation.name

    @admin.display(description="Download AVL validation report file")
    def download_report(self, instance):
        if instance.pk is None:
            return "Not available"
        if not instance.file:
            return "Empty"

        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:avl-validation-report", args=[instance.pk]),
            instance.file.name,
        )

    def download_validation_report(self, request, pk):
        if request.user.is_anonymous or not request.user.is_superuser:
            return HttpResponseForbidden("not admin user", content_type="text/html")
        report = get_object_or_404(AVLValidationReport, pk=pk)
        response = FileResponse(report.file.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={report.file.name}"
        return response


@admin.register(AVLSchemaValidationReport)
class AVLSchemaValidationReportAdmin(admin.ModelAdmin):
    formfield_overrides = {models.FileField: {"widget": CustomAdminFileWidget}}
    list_display = (
        "dataset_id",
        "organisation_name",
        "download_report",
        "error_count",
        "created",
    )
    search_fields = ("revision__dataset__id", "revision__dataset__organisation__name")
    fields = (
        "dataset_id",
        "organisation_name",
        "download_report",
        "file",
        "revision",
        "error_count",
        "created",
    )
    readonly_fields = (
        "id",
        "dataset_id",
        "organisation_name",
        "download_report",
    )

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "download-avl-schema-report/<int:pk>",
                self.download_schema_report,
                name="avl-schema-report",
            ),
        ]
        return urls

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .select_related("revision", "revision__dataset__organisation")
        )

    @admin.display(ordering="revision__dataset__id")
    def dataset_id(self, instance):
        return instance.revision.dataset_id

    @admin.display(ordering="revision__dataset__organisation__name")
    def organisation_name(self, instance):
        return instance.revision.dataset.organisation.name

    @admin.display(description="Download AVL schema validation report file")
    def download_report(self, instance):
        if instance.pk is None:
            return "Not available"
        if not instance.file:
            return "Empty"

        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:avl-schema-report", args=[instance.pk]),
            instance.file.name,
        )

    def download_schema_report(self, request, pk):
        if request.user.is_anonymous or not request.user.is_superuser:
            return HttpResponseForbidden("not admin user", content_type="text/html")
        report = get_object_or_404(AVLSchemaValidationReport, pk=pk)
        response = FileResponse(report.file.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={report.file.name}"
        return response


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


@admin.register(PostPublishingCheckReport)
class PostPublishingCheckReportAdmin(admin.ModelAdmin):
    form = PostPublishingCheckReportAdminForm
    formfield_overrides = {models.FileField: {"widget": CustomAdminFileWidget}}
    list_display = (
        "dataset_id",
        "granularity",
        "created",
        "download_report",
        "vehicle_activities_analysed",
        "vehicle_activities_completely_matching",
    )
    readonly_fields = ("download_report",)
    fields = (
        "dataset",
        "granularity",
        "created",
        "download_report",
        "file",
        "vehicle_activities_analysed",
        "vehicle_activities_completely_matching",
    )
    search_fields = ("dataset__id",)

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "download-ppc-report/<int:pk>",
                self.download_ppc_report,
                name="post-publishing-check-report",
            ),
        ]
        return urls

    def download_report(self, instance):
        if instance.pk is None:
            return "Not available"
        if not instance.file:
            return "Empty"

        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:post-publishing-check-report", args=[instance.pk]),
            instance.file.name,
        )

    def download_ppc_report(self, request, pk):
        if request.user.is_anonymous or not request.user.is_superuser:
            return HttpResponseForbidden("not admin user", content_type="text/html")
        report = get_object_or_404(PostPublishingCheckReport, pk=pk)
        response = FileResponse(report.file.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={report.file.name}"
        return response
