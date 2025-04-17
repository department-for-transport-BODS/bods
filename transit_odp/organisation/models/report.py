from django_extensions.db.models import TimeStampedModel
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.postgres.fields import ArrayField


class ComplianceReport(TimeStampedModel):
    class Meta(TimeStampedModel.Meta):
        ordering = ("registration_number",)

    registration_number = models.CharField(
        _("Registration:Service Number"), max_length=255, db_index=True
    )
    service_number = models.CharField(
        _("Registration:Service Number"), max_length=64, db_index=True
    )
    scope_status = models.CharField(_("Scope Status"), max_length=64, null=True)
    seasonal_status = models.CharField(_("Seasonal Status"), max_length=64, null=True)
    organisation_name = models.CharField(
        _("Published Organisation Name"), max_length=512, null=True
    )
    overall_requires_attention = models.CharField(
        _("Overall Require Attention"), max_length=64, null=True
    )
    requires_attention = models.CharField(
        _("Timetable Require Attention"), max_length=64, null=True
    )
    published_status = models.CharField(
        _("Timetables Published Status"), max_length=64, null=True
    )
    staleness_status = models.CharField(
        _("Timetables Timeliness Status"), max_length=64, null=True
    )
    critical_dq_issues = models.CharField(
        _("Timetables critical DQ issues"), max_length=64, null=True
    )
    dataset_id = models.IntegerField(_("Timetables Data set ID"), null=True)
    filename = models.CharField(_("TXC:Filename"), max_length=1024, null=True)
    national_operator_code = models.CharField(
        _("TXC:Filename"), max_length=64, null=True
    )
    last_modified_date = models.DateField(
        _("TXC:Last Modified Date"), null=True, blank=True
    )
    effective_stale_date_from_last_modified = models.DateField(
        _("Date when timetable data is over 1 year old"), null=True, blank=True
    )
    operating_period_end_date = models.DateField(
        _("TXC:Operating Period End Date"), null=True, blank=True
    )
    effective_stale_date_from_otc_effective = models.DateField(
        _("Date Registration variation needs to be published"), null=True, blank=True
    )
    date_42_day_look_ahead = models.DateField(
        _("Date for complete 42 day look ahead"), null=True, blank=True
    )
    effective_seasonal_start = models.DateField(
        _("Date seasonal service should be published"), null=True, blank=True
    )
    seasonal_start = models.DateField(_("Seasonal Start Date"), null=True, blank=True)
    seasonal_end = models.DateField(_("Seasonal End Date"), null=True, blank=True)
    avl_requires_attention = models.CharField(
        _("AVL requires attention"), max_length=64, null=True
    )
    avl_published_status = models.CharField(
        _("AVL Published Status"), max_length=64, null=True
    )
    error_in_avl_to_timetable_matching = models.CharField(
        _("Error in AVL to Timetable Matching"), max_length=64, null=True
    )
    fares_requires_attention = models.CharField(
        _("Fares requires attention"), max_length=64, null=True
    )
    fares_published_status = models.CharField(
        _("Fares Published Status"), max_length=64, null=True
    )
    fares_timeliness_status = models.CharField(
        _("Fares Timeliness Status"), max_length=64, null=True
    )
    fares_compliance_status = models.CharField(
        _("Fares Compliance Status"), max_length=64, null=True
    )
    fares_dataset_id = models.IntegerField(_("Fares Data set ID"), null=True)
    fares_filename = models.CharField(_("NETEX:Filename"), max_length=1024, null=True)
    fares_last_modified_date = models.DateField(
        _("NETEX:Last Modified Date"), null=True, blank=True
    )
    fares_effective_stale_date_from_last_modified = models.DateField(
        _("Date when fares data is over 1 year old"), null=True, blank=True
    )
    fares_operating_period_end_date = models.DateField(
        _("NETEX:Operating Period End Date"), null=True, blank=True
    )
    operator_name = models.CharField(
        _("Registration:Operator Name"), max_length=512, null=True
    )
    otc_licence_number = models.CharField(
        _("Registration:Licence Number"), max_length=64, null=True
    )
    service_type_description = models.CharField(
        _("Registration:Service Type Description"), max_length=64, null=True
    )
    variation_number = models.CharField(
        _("Registration:Variation Number"), max_length=64, null=True
    )
    expiry_date = models.DateField(_("Registration:Expiry Date"), null=True, blank=True)
    effective_date = models.DateField(
        _("Registration:Effective Date"), null=True, blank=True
    )
    received_date = models.DateField(
        _("Registration:Received Date"), null=True, blank=True
    )
    traveline_region = models.CharField(
        _("Traveline Region"), max_length=1024, null=True, blank=True
    )
    local_authority_ui_lta = models.CharField(
        _("Local Transport Authority"), max_length=1024, null=True, blank=True
    )

    # Publishing organisation and actual organisation can be differentt
    # Values will be use full in case of frenchise organisation
    publish_organisation_id = models.IntegerField(
        _("Publish Organisation ID"), null=True, db_index=True
    )
    licence_organisation_id = models.IntegerField(
        _("Licence Organisation ID"), null=True, db_index=True
    )
    licence_organisation_name = models.CharField(
        _("Licence Organisation Name"), max_length=512, null=True
    )
    local_authorities_ids = ArrayField(
        models.CharField(
            _("Local Transport Authority IDs"),
            blank=True,
            max_length=100,
            db_index=True,
        ),
        null=True,
    )
