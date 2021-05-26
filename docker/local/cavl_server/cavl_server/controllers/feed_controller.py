import http

import connexion
import six
from cavl_server import util
from cavl_server.models.feed import Feed  # noqa: E501
from cavl_server.models.inline_response201 import InlineResponse201  # noqa: E501
from flask import current_app, make_response


def add_feed(body):  # noqa: E501
    """Adds a new feed

     # noqa: E501

    :param body: Feed object that needs to be added to the consumer config
    :type body: dict | bytes

    :rtype: InlineResponse201
    """
    if connexion.request.is_json:
        body = Feed.from_dict(connexion.request.get_json())  # noqa: E501
        print(body)

        # return id
        feed_id = body.id

        return InlineResponse201(id=feed_id)

    response = make_response("", http.HTTPStatus.METHOD_NOT_ALLOWED)
    response.mimetype = current_app.config["JSONIFY_MIMETYPE"]
    return response


def delete_feed(feed_id):  # noqa: E501
    """Deletes the feed with the specified ID

     # noqa: E501

    :param feed_id: The ID of the feed to delete
    :type feed_id: int

    :rtype: None
    """
    response = make_response("", http.HTTPStatus.NO_CONTENT)
    response.mimetype = current_app.config["JSONIFY_MIMETYPE"]
    return response


def get_feed(feed_id):  # noqa: E501
    """Gets a feed by ID

    Returns a single feed config # noqa: E501

    :param feed_id: The ID of feed to return
    :type feed_id: int

    :rtype: Feed
    """
    response = make_response("", http.HTTPStatus.NO_CONTENT)
    response.mimetype = current_app.config["JSONIFY_MIMETYPE"]
    return response


def get_feeds():  # noqa: E501
    """Gets a list of feeds

     # noqa: E501


    :rtype: List[Feed]
    """
    return []


def update_feed_with_form(feed_id, body=None):  # noqa: E501
    """Updates an existing feed with the specified ID with form data

     # noqa: E501

    :param feed_id: The ID of feed to update
    :type feed_id: int
    :param body:
    :type body: dict | bytes

    :rtype: None
    """
    if connexion.request.is_json:
        body = Body.from_dict(connexion.request.get_json())  # noqa: E501
    return "do some magic!"
