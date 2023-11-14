from django.urls import path
from django.contrib import admin
from django.http import FileResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils.html import format_html

from transit_odp.pipelines.models import SchemaDefinition


@admin.register(SchemaDefinition)
class SchemaDefinitionAdmin(admin.ModelAdmin):
    list_display = fields = (
        "category",
        "created",
        "modified",
        "checksum",
        "download_link",
    )
    actions = None

    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path(
                "download-file/<int:pk>",
                self.download_file,
                name="pipelines_schema_download-file",
            ),
        ]
        return urls

    @admin.display(description="Download Zip")
    def download_link(self, instance):
        return format_html(
            '<a href="{}">{}</a>',
            reverse("admin:pipelines_schema_download-file", args=[instance.pk]),
            instance.schema.name,
        )

    def download_file(self, request, pk):
        if request.user.is_anonymous or not request.user.is_superuser:
            return HttpResponseForbidden("not admin user", content_type="text/html")
        zip_ = SchemaDefinition.objects.get(pk=pk)
        response = FileResponse(zip_.schema.open("rb"), as_attachment=True)
        response["Content-Disposition"] = f"attachment; filename={zip_.schema.name}"
        return response

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
