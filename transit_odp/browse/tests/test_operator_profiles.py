import pytest
from django.conf import settings
from django_hosts import reverse

from config.hosts import DATA_HOST
from transit_odp.browse.forms import OperatorFeedbackForm
from transit_odp.organisation.factories import OrganisationFactory
from transit_odp.users.constants import OrgAdminType, SiteAdminType
from transit_odp.users.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestOperatorFeedbackView:
    view_name = "contact-operator"

    @pytest.fixture()
    def org(self, user: settings.AUTH_USER_MODEL):
        UserFactory(account_type=SiteAdminType)
        org = OrganisationFactory()
        UserFactory(account_type=OrgAdminType, organisations=(org,))
        org.key_contact = user
        org.save()
        return org

    def test_feedback_form_is_rendered(self, user, data_client, org):
        data_client.force_login(user=user)

        contact_operator_page = reverse(
            self.view_name, kwargs={"pk": org.id}, host=DATA_HOST
        )

        back_url = reverse("operator-detail", kwargs={"pk": org.id}, host=DATA_HOST)
        session = data_client.session
        session["back_url"] = back_url
        session.save()

        response = data_client.get(contact_operator_page)

        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name
            == "browse/operators/contact_operator.html"
        )
        assert isinstance(response.context_data["form"], OperatorFeedbackForm)
        assert response.context_data["back_url"] == back_url

    def test_success_page(self, user, data_client, org):
        data_client.force_login(user=user)
        feedback_operator_success = reverse(
            "feedback-operator-success", kwargs={"pk": org.id}, host=DATA_HOST
        )
        back_url = reverse("operators", host=DATA_HOST)
        session = data_client.session
        session["back_url"] = back_url
        session.save()

        response = data_client.get(feedback_operator_success)
        assert response.status_code == 200
        assert (
            response.context_data["view"].template_name
            == "browse/operators/contact_operator_success.html"
        )
        assert response.context_data["back_url"] == back_url

    def test_feedback_is_sent_to_publisher_by_consumer(
        self, mailoutbox, user, org, data_client
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, args=[org.id], host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "anonymous": False,
            },
            follow=True,
        )

        org_users = org.users.filter(account_type=OrgAdminType)
        org_users_emails = [org_user["email"] for org_user in org_users.values()]
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[2]
        assert (
            m.subject
            == f"Bus Open Data feedback: {org.name} has received a feedback message"
        )
        assert f"{user.email}" in m.body
        assert f"{org.name}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == org_users_emails

    def test_feedback_is_sent_to_publisher_anonymously(
        self, mailoutbox, user, data_client, org
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, kwargs={"pk": org.id}, host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
                "anonymous": True,
            },
            follow=True,
        )
        org_users = org.users.filter(account_type=OrgAdminType)
        org_users_emails = [org_user["email"] for org_user in org_users.values()]
        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[2]
        assert (
            m.subject
            == f"Bus Open Data feedback: {org.name} has received a feedback message"
        )
        assert "Anonymous" in m.body
        assert f"{org.name}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == org_users_emails

    def test_feedback_is_sent_to_admins_by_consumer(
        self, mailoutbox, user, org, data_client
    ):
        data_client.force_login(user=user)
        url = reverse(self.view_name, kwargs={"pk": org.id}, host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            },
            follow=True,
        )

        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[0]
        assert m.subject == "Bus Open Data feedback: Your email copy (do not reply)"
        assert f"{org.name}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) != [org.key_contact.email]

    def test_copy_feedback_to_consumer_by_consumer(
        self, mailoutbox, user, org, data_client
    ):
        data_client.force_login(user=user)

        url = reverse(self.view_name, kwargs={"pk": org.id}, host=DATA_HOST)

        response = data_client.post(
            url,
            data={
                "feedback": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            },
            follow=True,
        )

        assert response.status_code == 200
        assert len(mailoutbox) == 3
        m = mailoutbox[1]
        assert m.subject == "Bus Open Data feedback: Your email copy (do not reply)"
        assert f"{org.name}" in m.body
        assert m.from_email == settings.DEFAULT_FROM_EMAIL
        assert list(m.to) == [user.email]
