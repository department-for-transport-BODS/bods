"""Some fixture methods."""
import os

import pytest
from crispy_forms.helper import FormHelper
from tests.utils import get_rendered_template, render_attempted_output


@pytest.fixture(scope="session")
def output_test_path(pytestconfig):
    """Return absolute path to test outputs directory."""
    return os.path.join(pytestconfig.rootdir.strpath, "tests", "output")


@pytest.fixture(scope="session")
def rendered_template():
    """Return callable function to render form template."""
    return get_rendered_template


@pytest.fixture(scope="session")
def render_output():
    """Return callable function to render output template."""
    return render_attempted_output


@pytest.fixture(scope="function")
def helper():
    helper = FormHelper()
    return helper
