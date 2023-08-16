from unittest.mock import MagicMock, patch
from requests import RequestException

from transit_odp.disruptions.tasks import task_create_sirisx_zipfile


@patch("transit_odp.disruptions.tasks.DisruptionsDataArchive")
@patch("transit_odp.disruptions.tasks.requests")
def test_task_create_sirisx_zipfile(mrequests, marchive):
    marchive.objects.last.return_value = None
    mresponse = MagicMock(content=b"test")
    mrequests.get.return_value = mresponse
    task_create_sirisx_zipfile()
    marchive.assert_called_once()

    marchive_obj = MagicMock()
    marchive.objects.last.return_value = marchive_obj
    task_create_sirisx_zipfile()
    marchive_obj.save.assert_called_once_with()


@patch("transit_odp.disruptions.tasks.DisruptionsDataArchive")
@patch("transit_odp.disruptions.tasks.requests")
def test_task_create_sirisx_zipfile_exception(mrequests, marchive):
    mrequests.get.side_effect = RequestException
    task_create_sirisx_zipfile()
    assert not marchive.objects.objects.last.called
