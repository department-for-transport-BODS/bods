from django.contrib import admin

from transit_odp.data_quality_service.models import Checks


@admin.register(Checks)
class ChecksAdmin(admin.ModelAdmin):
    model = Checks
    list_display = ["id", "observation", "importance", "category", "queue_name"]
    ordering = ["id"]
