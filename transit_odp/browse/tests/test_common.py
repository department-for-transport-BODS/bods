import csv
import datetime
import io
import zipfile
from logging import getLogger
from unittest.mock import Mock, patch
import random

import pytest
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from django.utils import timezone
from django_hosts import reverse
from freezegun import freeze_time

from config.hosts import DATA_HOST
from transit_odp.avl.factories import AVLValidationReportFactory
from transit_odp.avl.proxies import AVLDataset
from transit_odp.avl.tasks import cache_avl_compliance_status
from transit_odp.browse.tasks import task_create_data_catalogue_archive
from transit_odp.browse.tests.comments_test import (
    DATA_LONG_MAXLENGTH_WITH_CARRIAGE_RETURN,
    DATA_LONGER_THAN_MAXLENGTH,
    DATA_LONGER_THAN_MAXLENGTH_WITH_CARRIAGE_RETURN,
    DATA_SHORTER_MAXLENGTH_WITH_CARRIAGE_RETURN,
)
from transit_odp.browse.views.local_authority import (
    LocalAuthorityDetailView,
    LocalAuthorityView,
)
from transit_odp.browse.views.operators import OperatorDetailView, OperatorsView
from transit_odp.browse.views.timetable_views import (
    DatasetChangeLogView,
    DatasetDetailView,
)
from transit_odp.common.downloaders import GTFSFile
from transit_odp.common.forms import ConfirmationForm
from transit_odp.common.loggers import DatafeedPipelineLoggerContext, PipelineAdapter
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.fares.factories import FaresMetadataFactory
from transit_odp.feedback.models import Feedback
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.constants import DatasetType, FeedStatus
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
    DraftDatasetFactory,
)
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from transit_odp.organisation.factories import (
    OrganisationFactory,
    SeasonalServiceFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models import DatasetSubscription, Organisation
from transit_odp.otc.constants import API_TYPE_WECA
from transit_odp.otc.factories import (
    LicenceFactory,
    LicenceModelFactory,
    LocalAuthorityFactory,
    OperatorFactory,
    OperatorModelFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.pipelines.factories import (
    BulkDataArchiveFactory,
    ChangeDataArchiveFactory,
    DatasetETLTaskResultFactory,
)
from transit_odp.site_admin.models import ResourceRequestCounter
from transit_odp.users.factories import (
    AgentUserFactory,
    AgentUserInviteFactory,
    UserFactory,
)
from transit_odp.users.models import AgentUserInvite
from transit_odp.users.utils import create_verified_org_user
from transit_odp.browse.common import get_in_scope_in_season_lta_service_numbers

pytestmark = pytest.mark.django_db


def test_get_in_scope_in_season_lta_service_numbers():
    org = OrganisationFactory()
    total_services = 3
    licence_number = "PD5000229"
    service = []
    all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
    bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)

    otc_lic = LicenceModelFactory(number=licence_number)
    for code in all_service_codes:
        service.append(
            ServiceModelFactory(
                licence=otc_lic,
                registration_number=code.replace(":", "/"),
                effective_date=datetime.date(year=2020, month=1, day=1),
                service_number="line1|line2",
            )
        )

    ui_lta = UILtaFactory(name="Dorset County Council")

    local_authority = LocalAuthorityFactory(
        id="1",
        name="Dorset Council",
        ui_lta=ui_lta,
        registration_numbers=service,
    )

    AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

    today = timezone.now().date()
    month = timezone.now().date() + datetime.timedelta(weeks=4)
    two_months = timezone.now().date() + datetime.timedelta(weeks=8)

    # Create Seasonal Services - one in season, one out of season
    SeasonalServiceFactory(
        licence=bods_licence,
        start=today,
        end=month,
        registration_code=int(all_service_codes[2][-1:]),
    )
    SeasonalServiceFactory(
        licence=bods_licence,
        start=month,
        end=two_months,
        registration_code=int(all_service_codes[1][-1:]),
    )

    service_df = get_in_scope_in_season_lta_service_numbers([local_authority])
    assert len(service_df) == 4
    for linename in ["line1", "line2"]:
        assert linename in service_df["split_service_number"].unique()
