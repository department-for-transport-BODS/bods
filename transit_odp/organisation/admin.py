from django.contrib import admin

from transit_odp.organisation.models import (
    Dataset,
    DatasetRevision,
    OperatorCode,
    Organisation,
)
from transit_odp.pipelines.models import DatasetETLTaskResult


class OperatorCodeInline(admin.TabularInline):
    model = OperatorCode
    show_change_link = True
    extra = 0
    min_num = 1


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]

    inlines = [OperatorCodeInline]


class RevisionInLine(admin.TabularInline):
    model = DatasetRevision
    show_change_link = True
    max_num = 1
    readonly_fields = ("name",)
    fields = ("name", "transxchange_version")

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    search_fields = ["organisation__name", "id"]
    inlines = [RevisionInLine]

    def get_queryset(self, request):
        # organisation_name and contact_email are in __str__ so we need to
        # select these to stop the number of queries blowing up
        queryset = super().get_queryset(request)
        return queryset.select_related("organisation", "contact")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        restrict live revisions to revisions belonging to dataset
        """
        if db_field.name == "live_revision":
            dataset_id = request.resolver_match.kwargs["object_id"]
            kwargs["queryset"] = DatasetRevision.objects.filter(dataset_id=dataset_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(DatasetRevision)
class StuckRevisionAdmin(admin.ModelAdmin):
    search_fields = ["dataset__id"]
    list_display = (
        "name",
        "dataset_id",
        "latest_task_status",
        "latest_task_progress",
        "status",
        "modified",
        "created",
    )
    readonly_fields = ("dataset_id",)
    fields = ("name",)
    actions = ["action_set_to_error"]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .get_stuck_revisions()
            .order_by("created")
        )

    def action_set_to_error(self, request, revisions):
        for revision in revisions:
            task = revision.etl_results.order_by("id").last()
            task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
            task.additional_info = "Put into error state by Admin."
            task.save()

    action_set_to_error.short_description = "Set revision to error state."

    def latest_task_progress(self, instance):
        return instance.latest_task_progress

    def latest_task_status(self, instance):
        return instance.latest_task_status

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False
