from django.contrib import admin

from transit_odp.organisation.models import Dataset, OperatorCode, Organisation


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


# @admin.register(Feed)
# class FeedAdmin(admin.ModelAdmin):
#     # fieldsets = (("Feed", {"fields": ("feed_name", "organisation")}),)
#     list_display = ["name", "organisation"]
#     search_fields = ["name", "organisation"]

admin.site.register(Dataset)
