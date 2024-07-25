from django.contrib import admin, messages
from django.forms.models import BaseInlineFormSet

from transit_odp.organisation.constants import SUCCESS, DatasetType
from transit_odp.organisation.models import (
    Dataset,
    DatasetRevision,
    OperatorCode,
    Organisation,
)
from transit_odp.pipelines.models import DatasetETLTaskResult

PUBLISH_ERROR_MESSAGE = (
    "One or more of the revisions you have selected is not in draft state"
)


class OptionalAdminAreaInlineFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True


class AdminInline(admin.TabularInline):
    model = Organisation.admin_areas.through
    formset = OptionalAdminAreaInlineFormSet
    extra = 1
    min_num = 1
    show_change_link = True
    verbose_name = "Admin Area"
    verbose_name_plural = "Admin Areas"


class OperatorCodeInline(admin.TabularInline):
    model = OperatorCode
    show_change_link = True
    extra = 0
    min_num = 1


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ["name", "is_abods_global_viewer"]
    search_fields = ["name"]
    exclude = ["admin_areas"]

    inlines = [OperatorCodeInline, AdminInline]


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_filter = ["dataset_type", "live_revision__status"]
    list_display_links = (
        "id",
        "live_revision_name",
    )
    list_display = (
        "id",
        "live_revision_name",
        "dataset_type",
        "organisation_name",
        "dataset_status",
        "contact_email",
    )
    search_fields = ["organisation__name", "id"]
    readonly_fields = (
        "organisation_name",
        "contact_email",
        "avl_feed_status",
        "avl_feed_last_checked",
    )

    fieldsets = (
        ("Information", {"fields": ("organisation_name", "contact_email")}),
        ("Edit", {"fields": ("live_revision",)}),
        ("AVL", {"fields": ("avl_feed_status", "avl_feed_last_checked")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .select_related("organisation", "contact")
            .add_live_data()
        )

    def organisation_name(self, instance=None):
        return instance.organisation.name

    def contact_email(self, instance=None):
        return instance.contact.email

    def live_revision_name(self, instance=None):
        return instance.name

    def dataset_status(self, instance=None):
        return instance.status

    def dataset_type(self, instance: Dataset):
        return DatasetType(instance.dataset_type).name

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        restrict live revisions to revisions belonging to dataset
        """
        if db_field.name == "live_revision":
            dataset_id = request.resolver_match.kwargs["object_id"]
            kwargs["queryset"] = DatasetRevision.objects.filter(
                dataset_id=dataset_id
            ).order_by("id")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request, instance=None):
        return False


@admin.register(DatasetRevision)
class DatasetRevisionAdmin(admin.ModelAdmin):
    actions = ["publish_revisions"]
    ordering = ("id", "name")
    search_fields = ["dataset__id", "id", "name"]
    list_filter = ["dataset__dataset_type", "status", "is_published"]
    list_display = (
        "id",
        "name",
        "dataset_id",
        "is_published",
        "dataset_type",
        "status",
        "published_at",
        "modified",
        "created",
    )
    list_display_links = ("name",)

    readonly_fields = (
        "id",
        "name",
        "dataset_id",
        "filename",
        "url_link",
        "status",
        "published_at",
        "modified",
        "created",
        "description",
        "short_description",
        "comment",
        "is_published",
    )
    fieldsets = (
        (
            "Information",
            {
                "fields": (
                    "id",
                    "name",
                    "dataset_id",
                    "filename",
                    "url_link",
                    "status",
                    "published_at",
                    "modified",
                    "created",
                    "description",
                    "short_description",
                    "comment",
                    "is_published",
                ),
            },
        ),
    )
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request=request).select_related("dataset")

    def dataset_type(self, instance=None):
        return DatasetType(instance.dataset.dataset_type).name

    def filename(self, instance=None):
        return instance.upload_file.name

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def publish_revisions(self, request, queryset):
        if queryset.exclude(status=SUCCESS).exists():
            self.message_user(
                request=request, message=PUBLISH_ERROR_MESSAGE, level=messages.ERROR
            )
            return

        for revision in queryset:
            revision.publish(user=request.user)

    publish_revisions.short_description = "Publish selected datasets"


class StuckRevision(DatasetRevision):
    class Meta:
        proxy = True


class FaresStuckRevision(DatasetRevision):
    class Meta:
        proxy = True


@admin.register(StuckRevision)
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


@admin.register(FaresStuckRevision)
class FaresStuckRevisionAdmin(admin.ModelAdmin):
    """
    Class for the Fares stuck revision view, where admin users
    are able to set stuck revisions to an error state.
    """

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
            .get_fares_stuck_revisions()
            .order_by("created")
        )

    def latest_task_progress(self, instance):
        return instance.latest_task_progress

    def latest_task_status(self, instance):
        return instance.latest_task_status

    def action_set_to_error(self, request, revisions):
        for revision in revisions:
            task = revision.etl_results.order_by("id").last()
            task.to_error("dataset_validate", DatasetETLTaskResult.SYSTEM_ERROR)
            task.additional_info = "Put into error state by Admin."
            task.save()

    action_set_to_error.short_description = "Set revision to error state"

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False
