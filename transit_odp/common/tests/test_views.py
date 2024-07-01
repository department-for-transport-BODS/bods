from django.test import RequestFactory

from transit_odp.common.views import CoachDownloadView


def test_download_coach_data_view(self, request_factory: RequestFactory):
    """Test the coach download view and see if view is loaded with 200 status code
    as well as the template name is correct or not

    Args:
        request_factory (RequestFactory): Request Factory
    """
    request = request_factory.get(f"/coach/download")

    response = CoachDownloadView.as_view()(request)

    assert response.status_code == 200
    context = response.context_data
    assert context["view"].template_name == "common/coach_download.html"
