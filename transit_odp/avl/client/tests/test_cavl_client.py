from datetime import datetime
from http import HTTPStatus
from typing import Optional, Union
from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest
import requests
import requests_mock
import logging
from requests.exceptions import RequestException, ConnectTimeout

from transit_odp.avl.client import CAVLService
from transit_odp.avl.dataclasses import Feed, ValidationTaskResult
from transit_odp.avl.enums import AVLFeedStatus

CapLog = pytest.LogCaptureFixture

DUMMY_CAVL_URL = "http://www.dummy.com"


@contextmanager
def does_not_raise():
    yield


@pytest.fixture
def mock_datetime_now(monkeypatch):
    datetime_mock = MagicMock(wrap=datetime.datetime)
    datetime_mock.now.return_value = datetime.datetime(2022, 12, 12, 0, 0, 0)

    monkeypatch.setattr(datetime, "datetime", datetime_mock)


@pytest.fixture()
def cavl_service() -> CAVLService:
    """Overrides CAVL_URL env settings to use dummy test one."""

    c = CAVLService()
    c.CAVL_URL = DUMMY_CAVL_URL
    c.AVL_URL = DUMMY_CAVL_URL
    return c


@requests_mock.Mocker(kw="m")
class TestCAVLService:
    @pytest.mark.parametrize(
        "status, response_mock, expected_result, expected_message",
        [
            (
                HTTPStatus.CREATED,
                {},
                does_not_raise(),
                ["POST http://www.dummy.com/subscriptions 201"],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                dict(errors=["Bad request"]),
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 400",
                    "[CAVL] Couldn't register feed <id=1>. Response: {'errors': ['Bad request']}",
                ],
            ),
            (
                HTTPStatus.NOT_FOUND,
                dict(errors=["Not found"]),
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 404",
                    "[CAVL] Couldn't register feed <id=1>. Response: {'errors': ['Not found']}",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                dict(errors=["Server error"]),
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 500",
                    "[CAVL] Couldn't register feed <id=1>. Response: {'errors': ['Server error']}",
                ],
            ),
        ],
    )
    def test_register_feed(
        self,
        caplog,
        cavl_service: CAVLService,
        status: int,
        response_mock,
        expected_result,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions"
        kwargs["m"].post(url, json=response_mock, status_code=status)

        with expected_result:
            cavl_service.register_feed(
                feed_id=1,
                publisher_id=1,
                url="dummy_url",
                username="dummy_u",
                password="dummy_p",
                description="dummy_description",
                short_description="dummy_short_description",
            )

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "status, response_mock, expected_result, expected_message",
        [
            (
                HTTPStatus.NO_CONTENT,
                {},
                does_not_raise(),
                ["DELETE http://www.dummy.com/subscriptions/1 204"],
            ),
            (
                HTTPStatus.NOT_FOUND,
                dict(errors=["Not found"]),
                pytest.raises(RequestException),
                [
                    "DELETE http://www.dummy.com/subscriptions/1 404",
                    "[CAVL] Couldn't delete feed <id=1>. Response: {'errors': ['Not found']}",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                dict(errors=["Bad request"]),
                pytest.raises(RequestException),
                [
                    "DELETE http://www.dummy.com/subscriptions/1 400",
                    "[CAVL] Couldn't delete feed <id=1>. Response: {'errors': ['Bad request']}",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                dict(errors=["Server error"]),
                pytest.raises(RequestException),
                [
                    "DELETE http://www.dummy.com/subscriptions/1 500",
                    "[CAVL] Couldn't delete feed <id=1>. Response: {'errors': ['Server error']}",
                ],
            ),
        ],
    )
    def test_delete_feed(
        self,
        caplog,
        cavl_service: CAVLService,
        status: int,
        response_mock,
        expected_result,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions/1"
        kwargs["m"].delete(url, json=response_mock, status_code=status)

        with expected_result:
            cavl_service.delete_feed(feed_id=1)

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "status, response_mock, expected_result, expected_message",
        [
            (
                HTTPStatus.NO_CONTENT,
                {},
                does_not_raise(),
                ["PUT http://www.dummy.com/subscriptions/1 204"],
            ),
            (
                HTTPStatus.NOT_FOUND,
                dict(errors=["Not found"]),
                pytest.raises(RequestException),
                [
                    "PUT http://www.dummy.com/subscriptions/1 404",
                    "[CAVL] Couldn't update feed <id=1>. Response: {'errors': ['Not found']}",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                dict(errors=["Bad request"]),
                pytest.raises(RequestException),
                [
                    "PUT http://www.dummy.com/subscriptions/1 400",
                    "[CAVL] Couldn't update feed <id=1>. Response: {'errors': ['Bad request']}",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                dict(errors=["Server error"]),
                pytest.raises(RequestException),
                [
                    "PUT http://www.dummy.com/subscriptions/1 500",
                    "[CAVL] Couldn't update feed <id=1>. Response: {'errors': ['Server error']}",
                ],
            ),
        ],
    )
    def test_update_feed(
        self,
        caplog,
        cavl_service: CAVLService,
        status: int,
        response_mock,
        expected_result,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions/1"

        kwargs["m"].put(url, json=response_mock, status_code=status)

        with expected_result:
            cavl_service.update_feed(1, "dummy", "dummy", "dummy", "dummy", "dummy")

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.fixture
    def test_get_feed_response(
        self, caplog, cavl_service: CAVLService, **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions/1"
        kwargs["m"].get(
            url,
            json=dict(
                id="1",
                publisherId="1",
                status="live",
                apiKey="1",
            ),
            status_code=HTTPStatus.OK,
        )

        result = cavl_service.get_feed(1)

        assert result == Feed(
            id="1",
            publisher_id="1",
            status=AVLFeedStatus.live.value,
            last_avl_data_received_date_time=None,
            heartbeat_last_received_date_time=None,
            service_start_datetime=None,
            service_end_datetime=None,
            api_key="1",
        )

        assert [rec.message for rec in caplog.records] == [
            "GET http://www.dummy.com/subscriptions/1 200"
        ]

    @pytest.mark.parametrize(
        "status, response_mock, expected_result, expected_message",
        [
            (
                HTTPStatus.NOT_FOUND,
                dict(errors=["Not found"]),
                pytest.raises(RequestException),
                [
                    "GET http://www.dummy.com/subscriptions/1 404",
                    "[CAVL] Couldn't fetch feed <id=1>. Response: {'errors': ['Not found']}",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                dict(errors=["Bad request"]),
                pytest.raises(RequestException),
                [
                    "GET http://www.dummy.com/subscriptions/1 400",
                    "[CAVL] Couldn't fetch feed <id=1>. Response: {'errors': ['Bad request']}",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                dict(errors=["Server error"]),
                pytest.raises(RequestException),
                [
                    "GET http://www.dummy.com/subscriptions/1 500",
                    "[CAVL] Couldn't fetch feed <id=1>. Response: {'errors': ['Server error']}",
                ],
            ),
        ],
    )
    def test_get_feed_exceptions(
        self,
        caplog,
        cavl_service: CAVLService,
        status: int,
        response_mock,
        expected_result: Optional[Feed],
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions/1"
        kwargs["m"].get(url, json=response_mock, status_code=status)

        with expected_result:
            cavl_service.get_feed(1)

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.fixture
    def test_get_feeds_response(
        self, caplog, cavl_service: CAVLService, **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions"
        kwargs["m"].get(
            url,
            json=[
                dict(
                    id="1",
                    publisherId="1",
                    status="live",
                    apiKey="1",
                ),
                dict(
                    id="2",
                    publisherId="1",
                    status="inactive",
                    apiKey="2",
                ),
            ],
            status_code=HTTPStatus.OK,
        )

        result = cavl_service.get_feeds()

        assert result == [
            Feed(
                id="1",
                publisher_id="1",
                status=AVLFeedStatus.live.value,
                last_avl_data_received_date_time=None,
                heartbeat_last_received_date_time=None,
                service_start_datetime=None,
                service_end_datetime=None,
                api_key="1",
            ),
            Feed(
                id="2",
                publisher_id="1",
                status=AVLFeedStatus.inactive.value,
                last_avl_data_received_date_time=None,
                heartbeat_last_received_date_time=None,
                service_start_datetime=None,
                service_end_datetime=None,
                api_key="2",
            ),
        ]

        assert [rec.message for rec in caplog.records] == [
            "GET http://www.dummy.com/subscriptions 200"
        ]

    @pytest.mark.parametrize(
        "status, response_mock, expected_result, expected_message",
        [
            (
                HTTPStatus.NOT_FOUND,
                dict(errors=["Not found"]),
                pytest.raises(RequestException),
                [
                    "GET http://www.dummy.com/subscriptions 404",
                    "[CAVL] Couldn't fetch feeds. Response: {'errors': ['Not found']}",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                dict(errors=["Bad request"]),
                pytest.raises(RequestException),
                [
                    "GET http://www.dummy.com/subscriptions 400",
                    "[CAVL] Couldn't fetch feeds. Response: {'errors': ['Bad request']}",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                dict(errors=["Server error"]),
                pytest.raises(RequestException),
                [
                    "GET http://www.dummy.com/subscriptions 500",
                    "[CAVL] Couldn't fetch feeds. Response: {'errors': ['Server error']}",
                ],
            ),
        ],
    )
    def test_get_feeds_exceptions(
        self,
        caplog,
        cavl_service: CAVLService,
        status: int,
        response_mock,
        expected_result: list[Feed],
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions"
        kwargs["m"].get(url, json=response_mock, status_code=status)

        with expected_result:
            cavl_service.get_feeds()

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.fixture
    def test_validate_feed(
        self, caplog, cavl_service: CAVLService, mock_datetime_now, **kwargs
    ) -> None:
        caplog.set_level(logging.WARNING)
        url = DUMMY_CAVL_URL + "/feed/verify"
        response_mock = dict(
            url="dummy",
            username="dummy",
            created="2022-12-12 00:00:00",
            siriVersion="2.0",
        )
        kwargs["m"].put(url, json=response_mock, status_code=HTTPStatus.OK)

        expected_result = ValidationTaskResult(
            status="FEED_VALID",
            url="dummy",
            username="dummy",
            password="dummy",
            created=datetime(2022, 12, 12, 0, 0, 0),
            version="2.0",
        )

        result = cavl_service.validate_feed("dummy", "dummy", "dummy")

        assert result == expected_result
        assert [rec.message for rec in caplog.records] == []

    @pytest.mark.parametrize(
        "status, response_mock, expected_message",
        [
            (
                HTTPStatus.NOT_FOUND,
                dict(errors=["Not found"]),
                [
                    "PUT http://www.dummy.com/feed/verify 404",
                    "[CAVL] Couldn't validate feed <url=dummy>. Response: {'errors': ['Not found']}",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                dict(errors=["Bad request"]),
                [
                    "PUT http://www.dummy.com/feed/verify 400",
                    "[CAVL] Couldn't validate feed <url=dummy>. Response: {'errors': ['Bad request']}",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                dict(errors=["Server error"]),
                [
                    "PUT http://www.dummy.com/feed/verify 500",
                    "[CAVL] Couldn't validate feed <url=dummy>. Response: {'errors': ['Server error']}",
                ],
            ),
        ],
    )
    def test_validate_feed_exception(
        self,
        caplog,
        cavl_service: CAVLService,
        status: int,
        response_mock,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/feed/verify"

        kwargs["m"].put(url, json=response_mock, status_code=status)

        with pytest.raises(requests.RequestException):
            cavl_service.validate_feed("dummy", "dummy", "dummy")

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "method, http_method, endpoint, parameters, expected_log, expected_result",
        [
            (
                "register_feed",
                "post",
                "/subscriptions",
                [1, 1, "dummy", "dummy", "dummy", "dummy", "dummy"],
                ["[CAVL] Couldn't register feed <id=1>. Response: (empty)"],
                pytest.raises(ConnectTimeout),
            ),
            (
                "update_feed",
                "put",
                "/subscriptions/1",
                [1, "dummy", "dummy", "dummy", "dummy", "dummy"],
                ["[CAVL] Couldn't update feed <id=1>. Response: (empty)"],
                pytest.raises(ConnectTimeout),
            ),
            (
                "delete_feed",
                "delete",
                "/subscriptions/1",
                [1],
                ["[CAVL] Couldn't delete feed <id=1>. Response: (empty)"],
                pytest.raises(ConnectTimeout),
            ),
            (
                "get_feeds",
                "get",
                "/subscriptions",
                [],
                ["[CAVL] Couldn't fetch feeds. Response: (empty)"],
                pytest.raises(ConnectTimeout),
            ),
            (
                "get_feed",
                "get",
                "/subscriptions/1",
                [1],
                ["[CAVL] Couldn't fetch feed <id=1>. Response: (empty)"],
                pytest.raises(ConnectTimeout),
            ),
        ],
    )
    def test_methods_exception_handling(
        self,
        caplog,
        cavl_service: CAVLService,
        method: str,
        http_method: str,
        endpoint: str,
        parameters: list,
        expected_log: list[str],
        expected_result,
        **kwargs
    ) -> None:
        url = DUMMY_CAVL_URL + endpoint

        getattr(kwargs["m"], http_method)(url, exc=requests.exceptions.ConnectTimeout)

        with expected_result:
            getattr(cavl_service, method)(*parameters)

        assert [rec.message for rec in caplog.records] == expected_log
