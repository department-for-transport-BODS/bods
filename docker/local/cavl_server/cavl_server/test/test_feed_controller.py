# coding: utf-8

from __future__ import absolute_import

from cavl_server.models.body import Body  # noqa: E501
from cavl_server.models.feed import Feed  # noqa: E501
from cavl_server.models.inline_response201 import InlineResponse201  # noqa: E501
from cavl_server.test import BaseTestCase
from flask import json
from six import BytesIO


class TestFeedController(BaseTestCase):
    """FeedController integration test stubs"""

    def test_add_feed(self):
        """Test case for add_feed

        Adds a new feed
        """
        body = Feed()
        response = self.client.open(
            "/v0/feed",
            method="POST",
            data=json.dumps(body),
            content_type="application/json",
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_delete_feed(self):
        """Test case for delete_feed

        Deletes the feed with the specified ID
        """
        response = self.client.open(
            "/v0/feed/{feedId}".format(feed_id=56), method="DELETE"
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_get_feed(self):
        """Test case for get_feed

        Gets a feed by ID
        """
        response = self.client.open(
            "/v0/feed/{feedId}".format(feed_id=56), method="GET"
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_get_feeds(self):
        """Test case for get_feeds

        Gets a list of feeds
        """
        response = self.client.open("/v0/feed", method="GET")
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))

    def test_update_feed_with_form(self):
        """Test case for update_feed_with_form

        Updates an existing feed with the specified ID with form data
        """
        body = Body()
        response = self.client.open(
            "/v0/feed/{feedId}".format(feed_id=56),
            method="POST",
            data=json.dumps(body),
            content_type="application/json",
        )
        self.assert200(response, "Response body is : " + response.data.decode("utf-8"))


if __name__ == "__main__":
    import unittest

    unittest.main()
