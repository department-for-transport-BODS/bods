from typing import List


def get_bounding_box(bounding_box: List):
    """Returns a list of coordinates that form a bounding box from request args."""

    # Array query params can be passed in a few ways, this handles 2
    # of the most common array string "?=boundingBox=minLong,minLat... and
    # multi query params "?boundingBox=minLong&boundingBox=minLat...
    box = []
    if len(bounding_box) == 1:
        box_string = bounding_box[0]
        try:
            box = [float(coord.strip()) for coord in box_string.split(",") if coord]
        except ValueError:
            return box
    else:
        box = [float(coord) for coord in bounding_box]

    return box
