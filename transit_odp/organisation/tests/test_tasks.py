import pytest
import datetime
from django.utils import timezone
from unittest.mock import patch
from django.test import RequestFactory
from transit_odp.browse.tests.test_views import AVL_LINE_LEVEL_REQUIRE_ATTENTION

from transit_odp.dqs.factories import (
    ChecksFactory,
    ObservationResultsFactory,
    TaskResultsFactory,
)
from transit_odp.naptan.factories import AdminAreaFactory
from transit_odp.organisation.factories import (
    DatasetFactory,
    DatasetRevisionFactory,
    DraftDatasetFactory,
    OrganisationFactory,
    SeasonalServiceFactory,
    TXCFileAttributesFactory,
)
from transit_odp.organisation.models.organisations import Organisation
from transit_odp.organisation.tasks import task_precalculate_operator_sra
from transit_odp.otc.constants import API_TYPE_WECA
from transit_odp.otc.factories import (
    LicenceModelFactory,
    LocalAuthorityFactory,
    ServiceModelFactory,
    UILtaFactory,
)
from transit_odp.transmodel.factories import (
    ServiceFactory,
    ServicePatternFactory,
    ServicePatternStopFactory,
)
from transit_odp.users.factories import UserFactory
from transit_odp.organisation.factories import LicenceFactory as BODSLicenceFactory
from waffle.testutils import override_flag
from transit_odp.common.constants import FeatureFlags

pytestmark = pytest.mark.django_db


class TestOperatorPeriodicTask:
    @override_flag(FeatureFlags.OPERATOR_PREFETCH_SRA.value, active=True)
    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    def test_operator_timetable_stats_not_compliant(
        self, mock_avl_requires_attention, request_factory: RequestFactory
    ):
        org = OrganisationFactory()
        today = timezone.now().date()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)

        mock_avl_requires_attention.return_value = []

        total_services = 9
        licence_number = "PD5000229"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"Line:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)

        # Setup two TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )

        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=75),
            modification_datetime=timezone.now() - datetime.timedelta(days=50),
            line_names=[all_line_names[1]],
        )
        # Setup a draft TXCFileAttributes
        dataset2 = DraftDatasetFactory(organisation=org)
        TXCFileAttributesFactory(
            revision=dataset2.revisions.last(),
            service_code=all_service_codes[2],
            line_names=[all_line_names[2]],
        )

        live_revision = DatasetRevisionFactory(dataset=dataset2)

        # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[3],
            operating_period_end_date=None,
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            line_names=[all_line_names[3]],
        )

        # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[4],
            operating_period_end_date=datetime.date.today()
            - datetime.timedelta(weeks=105),
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            line_names=[all_line_names[4]],
        )

        # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[5],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            line_names=[all_line_names[5]],
        )

        # Create Seasonal Services - one in season, one out of season
        SeasonalServiceFactory(
            licence=bods_licence,
            start=today,
            end=month,
            registration_code=int(all_service_codes[6][-1:]),
        )
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[7][-1:]),
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes, start=0):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        request = request_factory.get("/operators/")
        request.user = UserFactory()
        task_precalculate_operator_sra()

        org_updated = Organisation.objects.filter(id=org.id).first()
        # One out of season seasonal service reduces in scope services to 8
        assert org_updated.total_inscope == 8
        # 2 non-stale, 6 requiring attention. 6/8 services requiring attention = 75%
        assert org_updated.timetable_sra == 6

    @override_flag(FeatureFlags.OPERATOR_PREFETCH_SRA.value, active=True)
    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    def test_operator_weca_timetable_stats_not_compliant(
        self, mock_avl_line_level_require_attention, request_factory: RequestFactory
    ):
        """
        Test Operator WECA details view stat with non complaint data
        in_scope_in_season.

        Count there are few which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        today = timezone.now().date()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        mock_avl_line_level_require_attention.return_value = []

        total_services = 9
        licence_number = "PD5000229"
        service_code_prefix = "1101000"
        atco_code = "110"
        registration_code_index = -len(service_code_prefix) - 1
        all_service_codes = [
            f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
        ]
        all_line_names = [f"Line{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)

        # Setup two TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )

        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=75),
            modification_datetime=timezone.now() - datetime.timedelta(days=50),
            line_names=[all_line_names[1]],
        )
        # Setup a draft TXCFileAttributes
        dataset2 = DraftDatasetFactory(organisation=org)
        TXCFileAttributesFactory(
            revision=dataset2.revisions.last(),
            service_code=all_service_codes[2],
            line_names=[all_line_names[2]],
        )

        live_revision = DatasetRevisionFactory(dataset=dataset2)

        # Setup a TXCFileAttributes that will be 'Stale - 12 months old'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[3],
            operating_period_end_date=None,
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            line_names=[all_line_names[3]],
        )

        # Setup a TXCFileAttributes that will be 'Stale - 42 day look ahead'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[4],
            operating_period_end_date=datetime.date.today()
            - datetime.timedelta(weeks=105),
            modification_datetime=timezone.now() - datetime.timedelta(weeks=100),
            line_names=[all_line_names[4]],
        )

        # Setup a TXCFileAttributes that will be 'Stale - OTC Variation'
        TXCFileAttributesFactory(
            revision=live_revision,
            service_code=all_service_codes[5],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            line_names=[all_line_names[5]],
        )

        # Create Seasonal Services - one in season, one out of season
        SeasonalServiceFactory(
            licence=bods_licence,
            start=today,
            end=month,
            registration_code=int(all_service_codes[6][registration_code_index:]),
        )
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[7][registration_code_index:]),
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    atco_code=atco_code,
                    api_type=API_TYPE_WECA,
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        task_precalculate_operator_sra()
        org_updated = Organisation.objects.filter(id=org.id).first()
        # One out of season seasonal service reduces in scope services to 8
        assert org_updated.total_inscope == 8
        # 2 non-stale, 6 requiring attention. 6/8 services requiring attention = 75%
        assert org_updated.timetable_sra == 6

    @override_flag(FeatureFlags.OPERATOR_PREFETCH_SRA.value, active=True)
    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    def test_operator_detail_timetable_stats_compliant(
        self, mock_avl_line_level, request_factory: RequestFactory
    ):
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        mock_avl_line_level.return_value = []

        total_services = 4
        licence_number = "PD5000123"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"line:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        # Setup three TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][-1:]),
        )
        # Create In Season Seasonal Service for live, up to date service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][-1:]),
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        task_precalculate_operator_sra()
        org_updated = Organisation.objects.filter(id=org.id).first()
        # One out of season seasonal service reduces in scope services to 3
        assert org_updated.total_inscope == 3
        # 3 services up to date, including one in season. 0/3 requiring attention = 0%
        assert org_updated.timetable_sra == 0

    @override_flag(FeatureFlags.OPERATOR_PREFETCH_SRA.value, active=True)
    @override_flag(FeatureFlags.DQS_REQUIRE_ATTENTION.value, active=True)
    def test_operator_detail_dqs_stats_compliant(self, request_factory: RequestFactory):
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)

        total_services = 4
        licence_number = "PD5000123"
        all_service_codes = [f"{licence_number}:{n}" for n in range(total_services)]
        all_line_names = [f"line:{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        # Setup three TXCFileAttributes that will be 'Up to Date'
        txcfileattribute1 = TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][-1:]),
        )
        # Create In Season Seasonal Service for live, up to date service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][-1:]),
        )

        # create transmodel servicepattern
        service_pattern = ServicePatternFactory(
            revision=dataset1.live_revision, line_name=txcfileattribute1.line_names[0]
        )

        # create transmodel service
        service = ServiceFactory(
            revision=dataset1.live_revision,
            name=all_line_names[0],
            service_code=all_service_codes[0],
            service_patterns=[service_pattern],
            txcfileattributes=txcfileattribute1,
        )

        # create transmodel servicepatternstop
        service_pattern_stop = ServicePatternStopFactory(
            service_pattern=service_pattern
        )

        # create DQS observation result
        check1 = ChecksFactory(queue_name="Queue1", importance="Critical")
        check2 = ChecksFactory(queue_name="Queue1")
        check1.importance = "Critical"

        taskresult = TaskResultsFactory(
            transmodel_txcfileattributes=txcfileattribute1,
            checks=check1,
        )
        observation_result = ObservationResultsFactory(
            service_pattern_stop=service_pattern_stop, taskresults=taskresult
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta)

        task_precalculate_operator_sra()
        org_updated = Organisation.objects.filter(id=org.id).first()
        print(org_updated.total_inscope)
        print(org_updated.timetable_sra)
        # One out of season seasonal service reduces in scope services to 3
        assert org_updated.total_inscope == 3
        assert org_updated.timetable_sra == 1  # DQS critical issues

    @override_flag(FeatureFlags.OPERATOR_PREFETCH_SRA.value, active=True)
    @patch(AVL_LINE_LEVEL_REQUIRE_ATTENTION)
    def test_operator_detail_weca_timetable_stats_compliant(
        self, avl_line_level_require_attention, request_factory: RequestFactory
    ):
        """Test Operator WECA details view stat with complaint data in_scope_in_season
        Count there are zero which required attention

        Args:
            request_factory (RequestFactory): Request Factory
        """
        org = OrganisationFactory()
        month = timezone.now().date() + datetime.timedelta(weeks=4)
        two_months = timezone.now().date() + datetime.timedelta(weeks=8)
        avl_line_level_require_attention.return_value = []

        total_services = 4
        licence_number = "PD5000123"
        service_code_prefix = "1101000"
        atco_code = "110"
        registration_code_index = -len(service_code_prefix) - 1
        all_service_codes = [
            f"{licence_number}:{service_code_prefix}{n}" for n in range(total_services)
        ]
        all_line_names = [f"line{n}" for n in range(total_services)]
        bods_licence = BODSLicenceFactory(organisation=org, number=licence_number)
        dataset1 = DatasetFactory(organisation=org)
        dataset2 = DatasetFactory(organisation=org)

        request = request_factory.get("/operators/")
        request.user = UserFactory()

        # Setup three TXCFileAttributes that will be 'Up to Date'
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[0],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[0]],
        )
        TXCFileAttributesFactory(
            revision=dataset1.live_revision,
            service_code=all_service_codes[1],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[1]],
        )
        TXCFileAttributesFactory(
            revision=dataset2.live_revision,
            service_code=all_service_codes[2],
            operating_period_end_date=datetime.date.today()
            + datetime.timedelta(days=50),
            modification_datetime=timezone.now(),
            line_names=[all_line_names[2]],
        )

        # Create Out of Season Seasonal Service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=month,
            end=two_months,
            registration_code=int(all_service_codes[3][registration_code_index:]),
        )
        # Create In Season Seasonal Service for live, up to date service
        SeasonalServiceFactory(
            licence=bods_licence,
            start=timezone.now().date(),
            end=month,
            registration_code=int(all_service_codes[2][registration_code_index:]),
        )

        otc_lic1 = LicenceModelFactory(number=licence_number)
        services = []
        for index, code in enumerate(all_service_codes):
            services.append(
                ServiceModelFactory(
                    licence=otc_lic1,
                    registration_number=code.replace(":", "/"),
                    effective_date=datetime.date(year=2020, month=1, day=1),
                    api_type=API_TYPE_WECA,
                    atco_code=atco_code,
                    service_number=all_line_names[index],
                )
            )

        ui_lta = UILtaFactory(name="UI_LTA")
        LocalAuthorityFactory(
            id="1", name="first_LTA", registration_numbers=services, ui_lta=ui_lta
        )
        AdminAreaFactory(traveline_region_id="SE", ui_lta=ui_lta, atco_code=atco_code)

        task_precalculate_operator_sra()
        org_updated = Organisation.objects.filter(id=org.id).first()
        # One out of season seasonal service reduces in scope services to 3
        assert org_updated.total_inscope == 3
        # 3 services up to date, including one in season. 0/3 requiring attention = 0%
        assert org_updated.timetable_sra == 0
