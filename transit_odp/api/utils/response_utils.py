from lxml.etree import Element, SubElement, tostring


def create_xml_error_response(error_msg, error_code):
    """Create an xml error string response.

    Args:
        error_msg: Text to appear in the error_description element.
        error_code: Text to appear in the error_code element.

    Returns
        An xml response string.

    """
    response = Element("response")

    error = SubElement(response, "error_description")
    error.text = error_msg

    error_code_element = SubElement(response, "error_code")
    error_code_element.text = f"{error_code}"
    return tostring(response)
