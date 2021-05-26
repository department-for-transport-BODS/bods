import http
import random
import uuid
from datetime import datetime

import connexion
import six
from cavl_server import util
from cavl_server.models.validation_task_result import ValidationTaskResult  # noqa: E501
from flask import current_app, make_response


def validate_feed(body):  # noqa: E501
    """Creates a validation task to validate a feed

     # noqa: E501

    :param body: ValidationTaskResult object that indicates the validity of the feed
    :type body: dict | bytes

    :rtype: ValidationTaskResult
    """
    if connexion.request.is_json:
        body = ValidationTaskResult.from_dict(
            connexion.request.get_json()
        )  # noqa: E501

        response = body
        response.status = "FEED_VALID"
        response.created = datetime.utcnow()

        return response

    response = make_response("", http.HTTPStatus.METHOD_NOT_ALLOWED)
    response.mimetype = current_app.config["JSONIFY_MIMETYPE"]
    return response
