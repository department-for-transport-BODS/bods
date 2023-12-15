from django.contrib import admin

from transit_odp.naptan.models import AdminArea, Locality, StopPoint


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_per_page = 30
    search_fields = ["gazetteer_id", "name"]
    list_display = ("gazetteer_id", "name", "easting", "northing")
    list_display_links = ("gazetteer_id", "name")

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def has_change_permission(self, request, instance=None):
        return False


@admin.register(AdminArea)
class AdminAreaAdmin(admin.ModelAdmin):
    list_per_page = 30
    search_fields = ["atco_code"]
    list_display = ("id", "name", "traveline_region_id", "atco_code", "ui_lta")
    list_display_links = ("id", "name")
    readonly_fields = ("name", "traveline_region_id", "atco_code")

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def has_change_permission(self, request, instance=None):
        return True


@admin.register(StopPoint)
class StopPointAdmin(admin.ModelAdmin):
    list_per_page = 30
    search_fields = ["atco_code"]
    list_display = (
        "atco_code",
        "naptan_code",
        "common_name",
        "street",
        "indicator",
        "latitude",
        "longitude",
        "locality_name",
        "admin_area_name",
        "stop_areas",
    )
    exclude = ("locality", "admin_area", "location")
    readonly_fields = (
        "atco_code",
        "naptan_code",
        "common_name",
        "street",
        "indicator",
        "latitude",
        "longitude",
        "locality_name",
        "admin_area_name",
        "stop_areas",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("admin_area", "locality")

    def locality_name(self, instance):
        if instance.locality is None:
            return None
        return instance.locality.name

    def admin_area_name(self, instance):
        if instance.admin_area is None:
            return None
        return instance.admin_area.name

    def latitude(self, instance):
        return instance.location[-1]

    def longitude(self, instance):
        return instance.location[0]

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def has_change_permission(self, request, instance=None):
        return False
