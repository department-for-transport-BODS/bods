import config.hosts
import pytest
from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView
from django_hosts.resolvers import get_host, reverse

from transit_odp.users.constants import AccountType
from transit_odp.users.views.mixins import (
    AgentOrgAdminViewMixin,
    OrgAdminViewMixin,
    OrgUserViewMixin,
    SiteAdminOrOrgAdminViewMixin,
    SiteAdminViewMixin,
)

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
class TestOrgUserViewMixin:
    redirect_url = reverse("users:home", host=config.hosts.PUBLISH_HOST)

    class DummyView(OrgUserViewMixin, TemplateView):
        template_name = "page.html"

    @pytest.mark.parametrize(
        "user__account_type", [AccountType.org_staff.value, AccountType.org_admin.value]
    )
    def test_user_has_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.PUBLISH_HOST)

        response = self.DummyView.as_view()(request)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "user__account_type",
        [AccountType.developer.value, AccountType.site_admin.value],
    )
    def test_user_does_not_have_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.PUBLISH_HOST)

        with pytest.raises(PermissionDenied):
            self.DummyView.as_view()(request)


@pytest.mark.django_db
class TestOrgAdminViewMixin:
    redirect_url = reverse("users:home", host=config.hosts.PUBLISH_HOST)

    class DummyView(OrgAdminViewMixin, TemplateView):
        template_name = "page.html"

    @pytest.mark.parametrize("user__account_type", [AccountType.org_admin.value])
    def test_user_has_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.PUBLISH_HOST)

        response = self.DummyView.as_view()(request)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "user__account_type",
        [
            AccountType.org_staff.value,
            AccountType.developer.value,
            AccountType.site_admin.value,
        ],
    )
    def test_user_does_not_have_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.PUBLISH_HOST)

        with pytest.raises(PermissionDenied):
            self.DummyView.as_view()(request)


@pytest.mark.django_db
class TestSiteAdminViewMixin:
    class DummyView(SiteAdminViewMixin, TemplateView):
        template_name = "page.html"

    @pytest.mark.parametrize("user__account_type", [AccountType.site_admin.value])
    def test_user_has_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.ADMIN_HOST)

        response = self.DummyView.as_view()(request)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "user__account_type",
        [
            AccountType.org_staff.value,
            AccountType.developer.value,
            AccountType.org_admin.value,
        ],
    )
    def test_user_does_not_have_permission(self, user, request_factory):
        # Set up
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.ADMIN_HOST)

        with pytest.raises(PermissionDenied):
            self.DummyView.as_view()(request)


@pytest.mark.django_db
class TestSiteAdminOrOrgAdminViewMixin:
    class DummyView(SiteAdminOrOrgAdminViewMixin, TemplateView):
        template_name = "page.html"

    @pytest.mark.parametrize(
        "user__account_type, host",
        [
            (AccountType.site_admin.value, config.hosts.ADMIN_HOST),
            (AccountType.org_admin.value, config.hosts.PUBLISH_HOST),
        ],
    )
    def test_user_has_permission(self, user, host, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(host)

        response = self.DummyView.as_view()(request)

        assert response.status_code == 200

    @pytest.mark.parametrize(
        "user__account_type, host",
        [
            # site admins cannot access publish host and visa versa
            (AccountType.site_admin.value, config.hosts.PUBLISH_HOST),
            (AccountType.org_admin.value, config.hosts.ADMIN_HOST),
            (AccountType.org_staff.value, config.hosts.PUBLISH_HOST),
            (AccountType.org_staff.value, config.hosts.ADMIN_HOST),
            (AccountType.developer.value, config.hosts.PUBLISH_HOST),
            (AccountType.developer.value, config.hosts.ADMIN_HOST),
        ],
    )
    def test_user_does_not_have_permission(self, user, host, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(host)

        with pytest.raises(PermissionDenied):
            self.DummyView.as_view()(request)


@pytest.mark.django_db
class TestAgentOrgAdminViewMixin:
    redirect_url = reverse("users:home", host=config.hosts.PUBLISH_HOST)

    class DummyView(AgentOrgAdminViewMixin, TemplateView):
        template_name = "page.html"

    @pytest.mark.parametrize(
        "user__account_type",
        [AccountType.org_admin.value, AccountType.agent_user.value],
    )
    def test_user_has_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.PUBLISH_HOST)
        response = self.DummyView.as_view()(request)
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "user__account_type",
        [
            AccountType.org_staff.value,
            AccountType.developer.value,
            AccountType.site_admin.value,
        ],
    )
    def test_user_does_not_have_permission(self, user, request_factory):
        request = request_factory.get("/fake-url")
        request.user = user
        request.host = get_host(config.hosts.PUBLISH_HOST)

        with pytest.raises(PermissionDenied):
            self.DummyView.as_view()(request)
