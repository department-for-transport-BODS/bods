import config.hosts
import pytest
from django.conf import settings
from django.urls import resolve
from django_hosts import reverse

pytestmark = pytest.mark.django_db


# TODO - move tests to top-level near hosts.py and test urls for each site


def test_my_account():
    host = config.hosts.DATA_HOST

    assert "/account/" in reverse("users:home", host=host)
    assert resolve("/account/", urlconf=settings.DATA_URLCONF).view_name == "users:home"


def test_settings():
    host = config.hosts.DATA_HOST
    assert "/account/settings/" in reverse("users:settings", host=host)
    assert (
        resolve("/account/settings/", urlconf=settings.DATA_URLCONF).view_name
        == "users:settings"
    )


def test_manage_users(user: settings.AUTH_USER_MODEL):
    host = config.hosts.PUBLISH_HOST
    root_url = "/account/manage/"

    assert f"{root_url}invite/" in reverse("users:invite", host=host)
    assert (
        resolve(root_url + "invite/", urlconf=settings.PUBLISH_URLCONF).view_name
        == "users:invite"
    )

    user_url = f"{root_url}{user.id}/"
    assert user_url + "archive/" in reverse(
        "users:archive", host=host, kwargs={"pk": user.id}
    )
    assert (
        resolve(f"{user_url}archive/", urlconf=settings.PUBLISH_URLCONF).view_name
        == "users:archive"
    )

    assert f"{user_url}activate/" in reverse(
        "users:activate", host=host, kwargs={"pk": user.id}
    )
    assert (
        resolve(f"{user_url}activate/", urlconf=settings.PUBLISH_URLCONF).view_name
        == "users:activate"
    )

    assert f"{user_url}re-invite/" in reverse(
        "users:re-invite", host=host, kwargs={"pk": user.id}
    )
    assert (
        resolve(f"{user_url}re-invite/", urlconf=settings.PUBLISH_URLCONF).view_name
        == "users:re-invite"
    )


def test_manage_feeds():
    host = config.hosts.DATA_HOST

    assert "/account/manage/" in reverse("users:feeds-manage", host=host)
    assert (
        resolve("/account/manage/", urlconf=settings.DATA_URLCONF).view_name
        == "users:feeds-manage"
    )


def test_manage_organisations():
    host = config.hosts.ADMIN_HOST
    urlconf = settings.ADMIN_URLCONF
    url = "/organisations/"
    pattern = "users:organisation-manage"

    assert url in reverse(pattern, host=host)
    assert resolve(url, urlconf=urlconf).view_name == pattern


def test_redirect():
    host = config.hosts.DATA_HOST

    assert "/account/~redirect/" in reverse("users:redirect", host=host)
    assert (
        resolve("/account/~redirect/", urlconf=settings.DATA_URLCONF).view_name
        == "users:redirect"
    )
