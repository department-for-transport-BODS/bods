import pytest

from transit_odp.data_quality.factories import ServiceLinkFactory, ServicePatternFactory
from transit_odp.data_quality.factories.transmodel import (
    ServicePatternServiceLinkFactory,
)
from transit_odp.data_quality.factories.warnings import (
    ServiceLinkMissingStopWarningFactory,
)
from transit_odp.data_quality.models import ServiceLinkMissingStopWarning
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    TXCFileAttributesFactory,
)

pytestmark = pytest.mark.django_db


def test_slms_annotates_associated_service_patterns():
    revision = DatasetRevisionFactory()
    common_service_link = ServiceLinkFactory()
    other_service_patterns = ServicePatternFactory.create_batch(10)
    associated_service_patterns = ServicePatternFactory.create_batch(3)
    TXCFileAttributesFactory(
        revision=revision,
        line_names=[
            sp.service.name.split(":")[0] for sp in associated_service_patterns
        ],
    )

    for sp in other_service_patterns + associated_service_patterns:
        ServicePatternServiceLinkFactory(
            service_pattern=sp, service_link=common_service_link
        )

    warning = ServiceLinkMissingStopWarningFactory(
        service_link=common_service_link, report__revision=revision
    )

    warnings = ServiceLinkMissingStopWarning.objects.add_line(warning.report.id)
    warning = warnings.first()
    # Its important that these two return the same line because they are used in the
    # list and detail view.
    assert warning.get_service_pattern().service.name == warning.line

    assert warning.line in [sp.service.name for sp in associated_service_patterns]
    assert warning.line not in [sp.service.name for sp in other_service_patterns]
