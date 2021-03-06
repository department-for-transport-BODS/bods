# coding: utf-8

"""
    CAVL Config API

    Used to configure feed consumers in the CAVL Service  # noqa: E501

    OpenAPI spec version: 0.1.0
    Contact: greg.brown@itoworld.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""

from __future__ import absolute_import

import unittest

import cavl_client
from cavl_client.rest import ApiException
from models.validation_task_result import ValidationTaskResult  # noqa: E501


class TestValidationTaskResult(unittest.TestCase):
    """ValidationTaskResult unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testValidationTaskResult(self):
        """Test ValidationTaskResult"""
        # FIXME: construct object with mandatory attributes with example values
        # model = cavl_client.models.validation_task_result.ValidationTaskResult()  # noqa: E501
        # Test
        model = cavl_client.models.validation_task_result.ValidationTaskResult(
            url="http://www.test-feed.com",
            username="acccount123",
            # No account_key
        )

        assert model.password is None


if __name__ == "__main__":
    unittest.main()
