"""Some dummy pinging to ensure demo urls are consistent.

WARNING: Keep this syncrhonized with enabled urls files
"""
import pytest

try:
    # Default 'reverse' path since Django1.10
    from django.urls import reverse
except ImportError:
    # 'reverse' path for Django<1.10
    from django.core.urlresolvers import reverse


@pytest.mark.parametrize(
    "url_name,url_args,url_kwargs",
    [
        ("home", [], {}),
        # Components
        ("components:home", [], {}),
        ("components:checkbox", [], {}),
        ("components:checkboxes", [], {}),
        ("components:text-input", [], {}),
        ("components:text-area", [], {}),
        # Examples
        ("examples:home", [], {}),
        ("examples:signup", [], {}),
        ("examples:question-page-with-label", [], {}),
        ("examples:question-page-with-legend", [], {}),
    ],
)
def test_ping_reverse_urlname(client, url_name, url_args, url_kwargs):
    """Ping reversed url names."""
    response = client.get(reverse(url_name, args=url_args, kwargs=url_kwargs))
    assert response.status_code == 200
