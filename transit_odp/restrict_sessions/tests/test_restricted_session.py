import config.hosts
import pytest
from django_hosts.resolvers import reverse

from transit_odp.users.constants import AccountType

pytestmark = pytest.mark.django_db


class TestRestrictedSession:
    host = config.hosts.PUBLISH_HOST
    url = reverse("users:settings", host=host)

    def test_two_users_can_log_in_with_different_sessions(
        self, user_factory, client_factory
    ):
        for _ in range(2):
            user = user_factory(account_type=AccountType.org_admin.value)
            client = client_factory(host=self.host)
            client.force_login(user=user)
            response = client.get(self.url)
            assert response.status_code == 200

    def test_user_can_only_have_one_session(self, user_factory, client_factory):
        user = user_factory(account_type=AccountType.org_admin.value)
        client1 = client_factory(host=self.host)
        client2 = client_factory(host=self.host)
        client1.force_login(user=user)
        response = client1.get(self.url)
        assert response.status_code == 200, "Check first client works as normal"

        client2.force_login(user=user)
        response = client2.get(self.url)
        assert response.status_code == 200, "Check second client also works as normal"

        response = client1.get(self.url)
        assert response.status_code == 302, "Check first client is now redirected..."
        assert response.url.startswith("/account/login/"), "...to the login page"
