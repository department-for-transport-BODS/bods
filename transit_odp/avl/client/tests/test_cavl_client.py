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
        "status, expected_result, expected_message",
        [
            (
                HTTPStatus.CREATED,
                does_not_raise(),
                ["POST http://www.dummy.com/subscriptions 201"],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 400",
                    "[CAVL] Couldn't register feed <id=1>",
                ],
            ),
            (
                HTTPStatus.NOT_FOUND,
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 404",
                    "[CAVL] Couldn't register feed <id=1>",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 500",
                    "[CAVL] Couldn't register feed <id=1>",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                pytest.raises(RequestException),
                [
                    "POST http://www.dummy.com/subscriptions 500",
                    "[CAVL] Couldn't register feed <id=1>",
                ],
            ),
        ],
    )
    def test_register_feed(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        status: int,
        expected_result: bool,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/subscriptions"
        kwargs["m"].post(url, status_code=status)

        with expected_result:
            assert (
                cavl_service.register_feed(
                    feed_id=1,
                    publisher_id=1,
                    url="dummy_url",
                    username="dummy_u",
                    password="dummy_p",
                    description="dummy_description",
                    short_description="dummy_short_description",
                )
                is not None
            )

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "status, expected_result, expected_message",
        [
            (HTTPStatus.NO_CONTENT, True, ["DELETE http://www.dummy.com/feed/1 204"]),
            (
                HTTPStatus.NOT_FOUND,
                False,
                [
                    "DELETE http://www.dummy.com/feed/1 404",
                    "[CAVL] Dataset 1 => Does not exist in CAVL Service.",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                False,
                [
                    "DELETE http://www.dummy.com/feed/1 400",
                    "[CAVL] Couldn't delete feed <id=1>",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                False,
                [
                    "DELETE http://www.dummy.com/feed/1 500",
                    "[CAVL] Couldn't delete feed <id=1>",
                ],
            ),
        ],
    )
    def test_delete_feed(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        status: int,
        expected_result: bool,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/feed/1"
        kwargs["m"].delete(url, status_code=status)

        result = cavl_service.delete_feed(feed_id=1)

        assert result == expected_result
        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "status, expected_result, expected_message",
        [
            (HTTPStatus.NO_CONTENT, True, ["POST http://www.dummy.com/feed/1 204"]),
            (
                HTTPStatus.NOT_FOUND,
                False,
                [
                    "POST http://www.dummy.com/feed/1 404",
                    "[CAVL] Couldn't update feed <id=1>",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                False,
                [
                    "POST http://www.dummy.com/feed/1 400",
                    "[CAVL] Couldn't update feed <id=1>",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                False,
                [
                    "POST http://www.dummy.com/feed/1 500",
                    "[CAVL] Couldn't update feed <id=1>",
                ],
            ),
        ],
    )
    def test_update_feed(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        status: int,
        expected_result: bool,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/feed/1"
        kwargs["m"].post(url, status_code=status)

        result = cavl_service.update_feed(1, "dummy", "dummy", "dummy")

        assert result == expected_result
        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "status, expected_result, expected_message",
        [
            (
                HTTPStatus.OK,
                Feed(id=1, publisher_id=1, url="dummy", username="dummy"),
                ["GET http://www.dummy.com/feed/1 200"],
            ),
            (
                HTTPStatus.NOT_FOUND,
                None,
                [
                    "GET http://www.dummy.com/feed/1 404",
                    "[CAVL] Couldn't fetch feed <id=1>",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                None,
                [
                    "GET http://www.dummy.com/feed/1 400",
                    "[CAVL] Couldn't fetch feed <id=1>",
                ],
            ),
        ],
    )
    def test_get_feed(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        status: int,
        expected_result: Optional[Feed],
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/feed/1"
        response_mock = dict(id=1, publisher_id=1, url="dummy", username="dummy")
        kwargs["m"].get(url, json=response_mock, status_code=status)

        result = cavl_service.get_feed(1)

        assert result == expected_result
        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "status, expected_result, expected_message",
        [
            (
                HTTPStatus.OK,
                [
                    Feed(id=1, publisher_id=1, url="dummy", username="dummy"),
                    Feed(id=2, publisher_id=1, url="dummy_2", username="dummy_2"),
                ],
                ["GET http://www.dummy.com/feed 200"],
            ),
            (
                HTTPStatus.NOT_FOUND,
                [],
                ["GET http://www.dummy.com/feed 404", "[CAVL] Couldn't fetch feeds"],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                [],
                ["GET http://www.dummy.com/feed 400", "[CAVL] Couldn't fetch feeds"],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                [],
                ["GET http://www.dummy.com/feed 500", "[CAVL] Couldn't fetch feeds"],
            ),
        ],
    )
    def test_get_feeds(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        status: int,
        expected_result: list[Feed],
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/feed"
        response_mock = [
            dict(id=1, publisher_id=1, url="dummy", username="dummy"),
            dict(id=2, publisher_id=1, url="dummy_2", username="dummy_2"),
        ]
        kwargs["m"].get(url, json=response_mock, status_code=status)

        result = cavl_service.get_feeds()

        assert result == expected_result
        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.fixture
    def test_validate_feed(
        self, caplog: CapLog, cavl_service: CAVLService, mock_datetime_now, **kwargs
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
        "status, expected_message",
        [
            (
                HTTPStatus.NOT_FOUND,
                [
                    "PUT http://www.dummy.com/feed/verify 404",
                    "[CAVL] Couldn't validate feed <url=dummy>",
                ],
            ),
            (
                HTTPStatus.BAD_REQUEST,
                [
                    "PUT http://www.dummy.com/feed/verify 400",
                    "[CAVL] Couldn't validate feed <url=dummy>",
                ],
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR,
                [
                    "PUT http://www.dummy.com/feed/verify 500",
                    "[CAVL] Couldn't validate feed <url=dummy>",
                ],
            ),
        ],
    )
    def test_validate_feed_exception(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        status: int,
        expected_message: list[str],
        **kwargs
    ) -> None:
        caplog.set_level(logging.DEBUG)
        url = DUMMY_CAVL_URL + "/feed/verify"
        response_mock = dict(
            url="dummy", username="dummy", created="2022-12-12 00:00:00"
        )
        kwargs["m"].put(url, json=response_mock, status_code=status)

        with pytest.raises(requests.RequestException):
            cavl_service.validate_feed("dummy", "dummy", "dummy")

        assert [rec.message for rec in caplog.records] == expected_message

    @pytest.mark.parametrize(
        "method, http_method, endpoint, parameters, expected_log, expected_result",
        [
            (
                "delete_feed",
                "delete",
                "/feed/1",
                [1],
                ["[CAVL] Couldn't delete feed <id=1>"],
                False,
            ),
            (
                "update_feed",
                "post",
                "/feed/1",
                [1, "dummy", "dummy", "dummy"],
                ["[CAVL] Couldn't update feed <id=1>"],
                False,
            ),
            (
                "get_feed",
                "get",
                "/feed/1",
                [1],
                ["[CAVL] Couldn't fetch feed <id=1>"],
                None,
            ),
            ("get_feeds", "get", "/feed", [], ["[CAVL] Couldn't fetch feeds"], []),
        ],
    )
    def test_methods_exception_handling(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        method: str,
        http_method: str,
        endpoint: str,
        parameters: list,
        expected_log: list[str],
        expected_result: Union[bool, None, list],
        **kwargs
    ) -> None:
        url = DUMMY_CAVL_URL + endpoint

        getattr(kwargs["m"], http_method)(url, exc=requests.exceptions.ConnectTimeout)

        result = getattr(cavl_service, method)(*parameters)

        assert result == expected_result
        assert [rec.message for rec in caplog.records] == expected_log

    # Modified exception handling tests for new AVL service as we are now raising an error instead of returning
    # False. As other CAVL service functions migrate to the new AVL service we will populate the below test case to
    # replace the old test case above
    @pytest.mark.parametrize(
        "method, http_method, endpoint, parameters, expected_log, expected_result",
        [
            (
                "register_feed",
                "post",
                "/subscriptions",
                [1, 1, "dummy", "dummy", "dummy", "dummy", "dummy"],
                ["[CAVL] Couldn't register feed <id=1>"],
                pytest.raises(ConnectTimeout),
            ),
        ],
    )
    def test_methods_exception_handling_new_avl(
        self,
        caplog: CapLog,
        cavl_service: CAVLService,
        method: str,
        http_method: str,
        endpoint: str,
        parameters: list,
        expected_log: list[str],
        expected_result: Union[bool, None, list],
        **kwargs
    ) -> None:
        url = DUMMY_CAVL_URL + endpoint

        getattr(kwargs["m"], http_method)(url, exc=requests.exceptions.ConnectTimeout)

        with expected_result:
            assert getattr(cavl_service, method)(*parameters) is not None

        assert [rec.message for rec in caplog.records] == expected_log
