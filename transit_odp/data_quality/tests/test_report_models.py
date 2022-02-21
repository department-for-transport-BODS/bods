import csv
import io
import zipfile
from io import TextIOWrapper

import pytest
from django.utils.timezone import now
from django_hosts.resolvers import reverse
from freezegun.api import freeze_time

from config.hosts import PUBLISH_HOST
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.data_quality.models.report import PTIValidationResult
from transit_odp.data_quality.pti.factories import ViolationFactory
from transit_odp.data_quality.pti.report import PTI_CSV_COLUMNS, UTF8
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.users.constants import OrgAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


@freeze_time("2030-12-25T12:05:05")
def test_from_pti_violations(pti_unenforced):
    revision = DatasetRevisionFactory()
    violations = [ViolationFactory()]

    PTIValidationResult.from_pti_violations(
        revision=revision, violations=violations
    ).save()

    validation_result = PTIValidationResult.objects.get(revision_id=revision.id)
    expected_filename = (
        f"BODS_TXC_validation_{revision.dataset.organisation.name}"
        f"_{revision.dataset_id}"
        f"_{now():%H_%M_%d%m%Y}.csv"
    )
    expected_zipname = f"pti_validation_revision_{revision.id}.zip"
    assert validation_result.report.name == expected_zipname
    with zipfile.ZipFile(validation_result.report, "r") as zf:
        assert expected_filename in zf.namelist()
        with zf.open(expected_filename, "r") as fp:
            reader = csv.reader(TextIOWrapper(fp, UTF8))
            columns, first = reader
            assert PTI_CSV_COLUMNS == tuple(columns)
            for violation in violations:
                assert [str(item) for item in violation.to_bods_csv()] == first


@freeze_time("2030-12-25T12:05:05")
def test_important_information_blank_after_pti_deadline(pti_enforced):
    revision = DatasetRevisionFactory()
    violations = [ViolationFactory()]

    PTIValidationResult.from_pti_violations(
        revision=revision, violations=violations
    ).save()

    validation_result = PTIValidationResult.objects.get(revision_id=revision.id)
    expected_filename = (
        f"BODS_TXC_validation_{revision.dataset.organisation.name}"
        f"_{revision.dataset_id}"
        f"_{now():%H_%M_%d%m%Y}.csv"
    )
    with zipfile.ZipFile(validation_result.report, "r") as zf:
        with zf.open(expected_filename, "r") as fp:
            reader = csv.reader(TextIOWrapper(fp, UTF8))
            columns, _ = reader
            assert PTI_CSV_COLUMNS == tuple(columns)
            for violation in violations:
                assert violation.to_bods_csv()[-1] == ""


@freeze_time("2030-12-25T12:05:05")
def test_pti_observations_filename(client_factory):
    revision = DatasetRevisionFactory()
    PTIObservationFactory.create_batch(5, revision=revision)

    org = OrganisationFactory.create()
    host = PUBLISH_HOST
    user = UserFactory(account_type=OrgAdminType, organisations=(org,))
    client = client_factory(host=host)
    client.force_login(user=user)

    url = reverse(
        "revision-pti-csv", kwargs={"pk": revision.dataset.id, "pk1": org.id}, host=host
    )
    expected_filename = (
        f"BODS_TXC_validation_{revision.dataset.organisation.name}"
        f"_{revision.dataset_id}"
        f"_{now():%H:%M_%d%m%Y}.csv"
    )
    response = client.get(url)
    response_file = io.BytesIO(b"".join(response.streaming_content))

    assert response.status_code == 200
    with zipfile.ZipFile(response_file, "r") as zout:
        assert expected_filename in zout.namelist()
