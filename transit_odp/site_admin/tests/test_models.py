import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import transaction
from django.test import RequestFactory

from transit_odp.site_admin.models import ResourceRequestCounter


pytestmark = pytest.mark.django_db


def test_counter_increments_for_authenticated_user(
    user_factory, django_capture_on_commit_callbacks
):
    user = user_factory()
    request = RequestFactory().get("/resource/path")
    request.user = user

    with django_capture_on_commit_callbacks(execute=True):
        ResourceRequestCounter.from_request(request)
        ResourceRequestCounter.from_request(request)

    counter = ResourceRequestCounter.objects.get(
        requestor=user,
        path_info="/resource/path",
    )
    assert counter.counter == 2


def test_counter_increments_for_anonymous_user(django_capture_on_commit_callbacks):
    request = RequestFactory().get("/resource/path")
    request.user = AnonymousUser()

    with django_capture_on_commit_callbacks(execute=True):
        ResourceRequestCounter.from_request(request)
        ResourceRequestCounter.from_request(request)

    counter = ResourceRequestCounter.objects.get(
        requestor=None,
        path_info="/resource/path",
    )
    assert counter.counter == 2


def test_counter_write_runs_after_transaction_commit(
    user_factory, django_capture_on_commit_callbacks
):
    user = user_factory()
    request = RequestFactory().get("/resource/path")
    request.user = user

    with django_capture_on_commit_callbacks(execute=False) as callbacks:
        with transaction.atomic():
            ResourceRequestCounter.from_request(request)
            assert ResourceRequestCounter.objects.count() == 0

    for callback in callbacks:
        callback()

    counter = ResourceRequestCounter.objects.get(
        requestor=user,
        path_info="/resource/path",
    )
    assert counter.counter == 1