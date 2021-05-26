from unittest.mock import Mock, patch

import config.hosts
import pytest
from cavl_client.rest import ApiException
from django_hosts.resolvers import reverse

from transit_odp.avl.views.dataset_archive import AVLFeedArchiveView
from transit_odp.organisation.factories import (
    AVLDatasetRevisionFactory,
    OrganisationFactory,
)
from transit_odp.users.factories import OrgStaffFactory
from transit_odp.users.views.mixins import OrgUserViewMixin

pytestmark = pytest.mark.django_db

AVL_VIEWS = "transit_odp.avl.views."


class TestAVLFeedArchiveViewDataset:
    host = config.hosts.PUBLISH_HOST

    def test_view_permission_mixin(self):
        assert issubclass(AVLFeedArchiveView, OrgUserViewMixin)

    @pytest.mark.skip("Doesn't work in the pipeline due to --numprocesses")
    @pytest.mark.parametrize(
        "mock_kwargs", ({"return_value": None}, {"side_effect": ApiException})
    )
    @patch(AVL_VIEWS + "dataset_archive.get_cavl_service")
    def test_archive_successful(self, get_service, client_factory, mock_kwargs):
        client = client_factory(host=self.host)
        mock_cavl = Mock()
        mock_cavl.delete_feed = Mock(**mock_kwargs)
        get_service.return_value = mock_cavl

        organisation = OrganisationFactory()
        user = OrgStaffFactory(organisations=(organisation,))
        dataset = AVLDatasetRevisionFactory(
            published_by=user, dataset__organisation=organisation
        )

        client.force_login(user=user)
        url = reverse(
            "avl:feed-archive", args=[organisation.id, dataset.id], host=self.host
        )
        success_url = reverse(
            "avl:feed-archive-success",
            args=[organisation.id, dataset.id],
            host=self.host,
        )

        response = client.post(url, data={"submit": "submit"})
        dataset.refresh_from_db()

        mock_cavl.delete_feed.assert_called_once_with(feed_id=dataset.id)
        assert dataset.status == "inactive"
        assert response.status_code == 302
        assert response.url == success_url
