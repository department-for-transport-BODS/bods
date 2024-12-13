# Generated by Django 4.2.14 on 2024-12-13 07:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data_quality", "0058_postschemaviolation"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fasttimingwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="fasttimingwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="fasttimingwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="fasttimingwarning",
            name="timings",
        ),
        migrations.AlterUniqueTogether(
            name="incorrectnocwarning",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="incorrectnocwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeyconflictwarning",
            name="conflict",
        ),
        migrations.RemoveField(
            model_name="journeyconflictwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeyconflictwarning",
            name="stops",
        ),
        migrations.RemoveField(
            model_name="journeyconflictwarning",
            name="vehicle_journey",
        ),
        migrations.RemoveField(
            model_name="journeydaterangebackwardswarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeydaterangebackwardswarning",
            name="vehicle_journey",
        ),
        migrations.RemoveField(
            model_name="journeyduplicatewarning",
            name="duplicate",
        ),
        migrations.RemoveField(
            model_name="journeyduplicatewarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeyduplicatewarning",
            name="vehicle_journey",
        ),
        migrations.RemoveField(
            model_name="journeystopinappropriatewarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeystopinappropriatewarning",
            name="stop",
        ),
        migrations.RemoveField(
            model_name="journeystopinappropriatewarning",
            name="vehicle_journeys",
        ),
        migrations.RemoveField(
            model_name="journeywithoutheadsignwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="journeywithoutheadsignwarning",
            name="vehicle_journey",
        ),
        migrations.AlterUniqueTogether(
            name="lineexpiredwarning",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="lineexpiredwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="lineexpiredwarning",
            name="service",
        ),
        migrations.RemoveField(
            model_name="lineexpiredwarning",
            name="vehicle_journeys",
        ),
        migrations.AlterUniqueTogether(
            name="linemissingblockidwarning",
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name="linemissingblockidwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="linemissingblockidwarning",
            name="service",
        ),
        migrations.RemoveField(
            model_name="linemissingblockidwarning",
            name="vehicle_journeys",
        ),
        migrations.RemoveField(
            model_name="servicelinkmissingstopwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="servicelinkmissingstopwarning",
            name="service_link",
        ),
        migrations.RemoveField(
            model_name="servicelinkmissingstopwarning",
            name="stops",
        ),
        migrations.RemoveField(
            model_name="slowlinkwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="slowlinkwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="slowlinkwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="slowlinkwarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="slowtimingwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="slowtimingwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="slowtimingwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="slowtimingwarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="stopincorrecttypewarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="stopincorrecttypewarning",
            name="service_patterns",
        ),
        migrations.RemoveField(
            model_name="stopincorrecttypewarning",
            name="stop",
        ),
        migrations.RemoveField(
            model_name="stopmissingnaptanwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="stopmissingnaptanwarning",
            name="service_patterns",
        ),
        migrations.RemoveField(
            model_name="stopmissingnaptanwarning",
            name="stop",
        ),
        migrations.RemoveField(
            model_name="timingbackwardswarning",
            name="from_stop",
        ),
        migrations.RemoveField(
            model_name="timingbackwardswarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timingbackwardswarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="timingbackwardswarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timingbackwardswarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="timingbackwardswarning",
            name="to_stop",
        ),
        migrations.RemoveField(
            model_name="timingdropoffwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timingdropoffwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="timingdropoffwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timingdropoffwarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="timingfirstwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timingfirstwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="timingfirstwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timingfirstwarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="timinglastwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timinglastwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="timinglastwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timinglastwarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="timingmissingpointwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timingmissingpointwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="timingmissingpointwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timingmissingpointwarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="timingmultiplewarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timingmultiplewarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timingmultiplewarning",
            name="timings",
        ),
        migrations.RemoveField(
            model_name="timingpickupwarning",
            name="report",
        ),
        migrations.RemoveField(
            model_name="timingpickupwarning",
            name="service_links",
        ),
        migrations.RemoveField(
            model_name="timingpickupwarning",
            name="timing_pattern",
        ),
        migrations.RemoveField(
            model_name="timingpickupwarning",
            name="timings",
        ),
        migrations.DeleteModel(
            name="FastLinkWarning",
        ),
        migrations.DeleteModel(
            name="FastTimingWarning",
        ),
        migrations.DeleteModel(
            name="IncorrectNOCWarning",
        ),
        migrations.DeleteModel(
            name="JourneyConflictWarning",
        ),
        migrations.DeleteModel(
            name="JourneyDateRangeBackwardsWarning",
        ),
        migrations.DeleteModel(
            name="JourneyDuplicateWarning",
        ),
        migrations.DeleteModel(
            name="JourneyStopInappropriateWarning",
        ),
        migrations.DeleteModel(
            name="JourneyWithoutHeadsignWarning",
        ),
        migrations.DeleteModel(
            name="LineExpiredWarning",
        ),
        migrations.DeleteModel(
            name="LineMissingBlockIDWarning",
        ),
        migrations.DeleteModel(
            name="ServiceLinkMissingStopWarning",
        ),
        migrations.DeleteModel(
            name="SlowLinkWarning",
        ),
        migrations.DeleteModel(
            name="SlowTimingWarning",
        ),
        migrations.DeleteModel(
            name="StopIncorrectTypeWarning",
        ),
        migrations.DeleteModel(
            name="StopMissingNaptanWarning",
        ),
        migrations.DeleteModel(
            name="TimingBackwardsWarning",
        ),
        migrations.DeleteModel(
            name="TimingDropOffWarning",
        ),
        migrations.DeleteModel(
            name="TimingFirstWarning",
        ),
        migrations.DeleteModel(
            name="TimingLastWarning",
        ),
        migrations.DeleteModel(
            name="TimingMissingPointWarning",
        ),
        migrations.DeleteModel(
            name="TimingMultipleWarning",
        ),
        migrations.DeleteModel(
            name="TimingPickUpWarning",
        ),
    ]
