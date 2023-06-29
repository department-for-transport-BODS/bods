from django.contrib import admin
from django import forms

from transit_odp.otc.models import Service, LocalAuthority


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = (
        "service_code",
        "service_type_description",
        "operator_name",
        "current_traffic_area",
        "licence_granted_date",
        "licence_expiry_date",
        "service_number",
        "start_point",
        "finish_point",
    )
    ordering = ("current_traffic_area",)

    search_fields = ("service_code",)
    list_filter = ("current_traffic_area",)

    exclude = ("operator", "licence", "registration_code")
    readonly_fields = (
        "operator_name",
        "licence_number",
        "registration_number",
        "service_type_description",
        "variation_number",
        "registration_status",
        "service_number",
        "current_traffic_area",
        "start_point",
        "finish_point",
        "via",
        "effective_date",
        "received_date",
        "end_date",
        "service_type_other_details",
        "description",
        "public_text",
        "short_notice",
        "subsidies_description",
        "subsidies_details",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request=request)
            .select_related("licence", "operator")
            .add_service_code()
            .add_licence_details()
            .add_operator_details()
        )

    def service_code(self, instance):
        return instance.service_code

    service_code.admin_order_field = "service_code"

    def operator_name(self, instance):
        return instance.operator_name

    def licence_granted_date(self, instance):
        return instance.granted_date

    def licence_expiry_date(self, instance):
        return instance.expiry_date

    def licence_number(self, instance):
        return instance.otc_licence_number

    def has_delete_permission(self, request, instance=None):
        return False

    def has_add_permission(self, request, instance=None):
        return False

    def has_change_permission(self, request, instance=None):
        return False


class LocalAuthoritiesForm(forms.ModelForm):
    class Meta:
        model = LocalAuthority
        fields = ["name", "ui_lta_name", "atco_code"]


@admin.register(LocalAuthority)
class LocalAuthorityAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = ("name", "ui_lta_name", "atco_code")
    search_fields = ("name", "ui_lta_name")
    list_filter = ("name",)
    ordering = ("name",)
    form = LocalAuthoritiesForm

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["name"]
        else:
            return []
