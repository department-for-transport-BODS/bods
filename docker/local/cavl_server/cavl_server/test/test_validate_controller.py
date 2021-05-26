# coding: utf-8

from __future__ import absolute_import

from cavl_server.models.validation_task_result import ValidationTaskResult  # noqa: E501
from cavl_server.test import BaseTestCase
from flask import json
from six import BytesIO


class TestValidateController(BaseTestCase):
    """ValidateController integration test stubs"""

    def test_validate_feed(self):
        """Test case for validate_feed

        Creates a validation task to validate a feed
        """
        body = ValidationTaskResult()
        response = self.client.open(
            "/v0/validate",
            method="POST",
            data=json.dumps(body),
            content_type="application/json",
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    import unittest

    unittest.main()
