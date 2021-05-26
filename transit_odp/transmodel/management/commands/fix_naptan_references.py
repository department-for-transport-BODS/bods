from django.core.management.base import BaseCommand
from django.db import transaction

from transit_odp.naptan.models import StopPoint
from transit_odp.transmodel.models import ServicePattern, ServicePatternStop

# Fixes broken:
#   ServicePatternStop.naptan_stop references
#   ServiceLink.from_stop and ServiceLink.to_stop references.
# Luckily we have the atco codes for the stops in the ServiceLinks, so we can
# rebuild the references using that information.


class Command(BaseCommand):
    help = "NOT FOR GENERAL USE: Runs part of a migration under development."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        with transaction.atomic():
            service_patterns = ServicePattern.objects.all()
            for index, service_pattern in enumerate(service_patterns):
                print(
                    "Fixing ServicePattern %d of %d"
                    % (index + 1, service_patterns.count())
                )

                # We need the existing list of ServicePatternStops. These are
                # the objects being fixed.
                stops = ServicePatternStop.objects.filter(
                    service_pattern=service_pattern
                )

                # Loop over the ServiceLinks, using the from-end to patch the stop
                for i, service_link in enumerate(service_pattern.service_links.all()):
                    from_naptan_stop = StopPoint.objects.get(
                        atco_code=service_link.from_atco
                    )

                    stop = stops[i]
                    stop.atco_code = service_link.from_atco
                    stop.naptan_stop = from_naptan_stop
                    stop.save()

                    # We can also fix the ServiceLink.from_stop now.
                    service_link.from_stop = from_naptan_stop

                    # Also fix the ServiceLink.to_stop
                    to_naptan_stop = StopPoint.objects.get(
                        atco_code=service_link.to_atco
                    )
                    service_link.to_stop = to_naptan_stop

                    service_link.save()

                # Fix the final stop on the to-end of the last ServiceLink
                stop = stops[i + 1]
                stop.atco_code = service_link.to_atco
                to_naptan_stop = StopPoint.objects.get(atco_code=service_link.to_atco)
                stop.naptan_stop = to_naptan_stop
                stop.save()
