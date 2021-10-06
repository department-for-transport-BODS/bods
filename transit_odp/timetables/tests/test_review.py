import pytest
from django.utils.timezone import now
from django_hosts import reverse

from config.hosts import PUBLISH_HOST
from transit_odp.data_quality.factories import DataQualityReportFactory
from transit_odp.data_quality.factories.report import PTIObservationFactory
from transit_odp.organisation.constants import TimetableType
from transit_odp.organisation.factories import (
    DatasetRevisionFactory,
    DatasetSubscriptionFactory,
)
from transit_odp.organisation.models import Dataset
from transit_odp.users.constants import AgentUserType, OrgAdminType
from transit_odp.users.factories import AgentUserInviteFactory, UserFactory
from transit_odp.users.models import AgentUserInvite

pytestmark = pytest.mark.django_db


class TestPublishReview:
    user_type = OrgAdminType
    host = PUBLISH_HOST

    def setup(self):
        self.user = UserFactory(account_type=self.user_type)
        self.revision = DatasetRevisionFactory(
            dataset__contact=self.user,
            dataset__dataset_type=TimetableType,
            dataset__organisation=self.user.organisations.first(),
            is_published=False,
        )
        DataQualityReportFactory(revision=self.revision)
        self.url = reverse(
            "revision-publish",
            host=self.host,
            kwargs={
                "pk": self.revision.dataset.id,
                "pk1": self.revision.dataset.organisation.id,
            },
        )

    def test_draft_revision_notifies_on_publish(self, client_factory, mailoutbox):
        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.post(
            self.url,
            data={
                "consent": "on",
                "submit": "submit",
            },
        )

        fished_out_dataset = Dataset.objects.get(id=self.revision.dataset.id)
        assert response.status_code == 302
        assert fished_out_dataset.live_revision == self.revision
        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Data set published"

    def test_draft_revision_notifies_on_publish_with_pti_errors(
        self, client_factory, mailoutbox
    ):
        PTIObservationFactory(revision=self.revision)
        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.post(
            self.url,
            data={
                "consent": "on",
                "submit": "submit",
            },
        )

        fished_out_dataset = Dataset.objects.get(id=self.revision.dataset.id)
        assert response.status_code == 302
        assert fished_out_dataset.live_revision == self.revision
        assert len(mailoutbox) == 1
        assert (
            mailoutbox[0].subject
            == "Action required – PTI validation report requires resolution"
        )

    def test_draft_notifies_on_publish_new_revision(self, client_factory, mailoutbox):
        self.revision.is_published = True
        self.revision.published_by = self.revision.dataset.contact
        self.revision.published_at = now()
        self.revision.save()
        DatasetSubscriptionFactory(dataset=self.revision.dataset)

        DatasetRevisionFactory(
            dataset=self.revision.dataset,
            is_published=False,
        )

        client = client_factory(host=self.host)
        client.force_login(self.user)

        response = client.post(
            self.url,
            data={
                "consent": "on",
                "submit": "submit",
            },
        )

        assert response.status_code == 302
        assert len(mailoutbox) == 2
        publisher, developer = mailoutbox
        assert publisher.subject == "Data set published"
        assert developer.subject == "Data set status changed"


class TestPublishReviewByAgent(TestPublishReview):
    user_type = AgentUserType

    def setup(self):
        super().setup()
        AgentUserInviteFactory(
            agent=self.user,
            organisation=self.user.organisations.first(),
            status=AgentUserInvite.ACCEPTED,
        )
