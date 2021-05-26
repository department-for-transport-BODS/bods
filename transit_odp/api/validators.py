from rest_framework.pagination import _positive_int

from transit_odp.common.utils.get_bounding_box import get_bounding_box

limit_query_param = "limit"
offset_query_param = "offset"
bbox_query_param = "boundingBox"


def validate_api_parameter_keys(query_params, valid_parameters):
    invalid_parameter_keys = []
    if len(query_params.keys()) > 0:
        input_parameters = list(query_params.keys())

        for parameter in input_parameters:
            if parameter not in valid_parameters:
                invalid_parameter_keys.append(parameter)
    return invalid_parameter_keys


def validate_api_parameter_values(query_params):
    invalid_parameter_values = []
    if len(query_params.keys()) > 0:
        input_parameters = list(query_params.keys())

        for parameter in input_parameters:
            if parameter == limit_query_param:
                try:
                    _positive_int(
                        query_params[limit_query_param],
                        strict=True,
                        cutoff=None,
                    )
                except (KeyError, ValueError):
                    invalid_parameter_values.append(limit_query_param)
            elif parameter == offset_query_param:
                try:
                    _positive_int(
                        query_params[offset_query_param],
                        strict=False,
                        cutoff=None,
                    )
                except (KeyError, ValueError):
                    invalid_parameter_values.append(offset_query_param)
            elif parameter == bbox_query_param:
                bounding_box = query_params.getlist("boundingBox", [])

                if bounding_box:
                    box = get_bounding_box(bounding_box)
                    if len(box) != 4:
                        invalid_parameter_values.append(bbox_query_param)

    return invalid_parameter_values
