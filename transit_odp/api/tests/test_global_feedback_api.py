import json

import pytest

from config import hosts
from transit_odp.feedback.models import Feedback

pytestmark = pytest.mark.django_db


def test_global_feedback_api_saves_feedback(client_factory):
    client = client_factory(host=hosts.ROOT_HOST)
    payload = {
        "satisfaction_rating": 4,
        "comment": "The service is easy to use.",
        "page_url": "https://www.example.com/changelog",
    }

    response = client.post(
        "/api/feedback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    feedback = Feedback.objects.get()
    assert feedback.satisfaction_rating == 4
    assert feedback.comment == payload["comment"]
    assert feedback.page_url == payload["page_url"]


def test_global_feedback_api_returns_form_validation_errors(client_factory):
    client = client_factory(host=hosts.ROOT_HOST)
    payload = {
        "satisfaction_rating": 6,
        "comment": "x" * 1201,
        "page_url": "https://www.example.com/changelog",
    }

    response = client.post(
        "/api/feedback/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "satisfaction_rating" in response.json()["field_errors"]
    assert "comment" in response.json()["field_errors"]
    assert Feedback.objects.count() == 0
