"""
client.py a module containing a client for requesting data from the BODS API.
"""
import io
import json
import zipfile
from http import HTTPStatus
from typing import Optional, Union
from urllib.parse import urlparse

import requests

from .constants import (
    BODS_API_URL,
    FARES_PATH,
    GTFS_RT_PATH,
    SIRI_VM_PATH,
    TIMETABLES_PATH,
    TXC_FILES_PATH,
)
from .models import (
    APIError,
    Fares,
    FaresResponse,
    Timetable,
    TimetableParams,
    TimetableResponse,
    TxcFileParams,
    TxcFileResponse,
)
from .models.avl import SIRIVMParams
from .models.fares import FaresParams


class BODSClient:
    """
    Client for requesting data from the BODS API.
    """

    def __init__(self, api_key: str, base_url: str = BODS_API_URL, version: str = "v1"):
        self.api_key = api_key
        if base_url.endswith("/"):
            self.base_url = base_url[:-1]
        else:
            self.base_url = base_url
        self.version = version

    def _make_request(self, path: str, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = 60

        if "params" in kwargs:
            kwargs["params"]["api_key"] = self.api_key
        else:
            kwargs["params"] = {"api_key": self.api_key}

        return requests.get(path, *args, **kwargs)

    @property
    def timetable_endpoint(self):
        return f"{self.base_url}/{self.version}/{TIMETABLES_PATH}/"

    @property
    def siri_vm_endpoint(self):
        return f"{self.base_url}/{self.version}/{SIRI_VM_PATH}/"

    @property
    def gtfs_rt_endpoint(self):
        return f"{self.base_url}/{self.version}/{GTFS_RT_PATH}/"

    @property
    def fares_endpoint(self):
        return f"{self.base_url}/{self.version}/{FARES_PATH}/"

    @property
    def siri_vm_zip_endpoint(self) -> str:
        parsed_url = urlparse(self.base_url)
        return f"{parsed_url.scheme}://{parsed_url.hostname}/avl/download/bulk_archive"

    @property
    def gtfs_rt_zip_endpoint(self) -> str:
        parsed_url = urlparse(self.base_url)
        return f"{parsed_url.scheme}://{parsed_url.hostname}/avl/download/gtfsrt"

    @property
    def txc_files_endpoint(self) -> str:
        return f"{self.base_url}/{self.version}/{TXC_FILES_PATH}/"

    def get_timetable_datasets(
        self, params: Optional[TimetableParams] = None
    ) -> Union[TimetableResponse, APIError]:
        """
        Fetches the data sets currently available in the BODS database.

        This only returns meta data about a data set including a url to
        the actual data set.

        Args:
            admin_areas: A list of NPTG ATCO Area codes.
            nocs: A list of National Operator Codes.
            status: Limit data sets with a specific status of published, error, expired,
            inactive.
            search: Return data sets with search term in the data set name, data set.
            description, organisation name, or admin name.
            modified_date: Get data sets created/updated after this date.
            start_date_start: Limit data sets to those with start dates after this date.
            start_date_end: Limit date sets to those with start dates before this date.
            end_date_start: Get data sets with end dates after this date.
            end_date_end: Get data sets with end dates before this date.
            limit: Maximum number of results to return per page.
            offset: Number to offset results by.
        """

        if params is None:
            params = TimetableParams()

        params = json.loads(params.json(by_alias=True, exclude_none=True))
        response = self._make_request(self.timetable_endpoint, params=params)

        if response.status_code == HTTPStatus.OK:
            return TimetableResponse(**response.json())
        return APIError(status_code=response.status_code, reason=response.content)

    def get_timetable_dataset(
        self, dataset_id: int
    ) -> Union[TimetableResponse, APIError]:
        """
        Get a single timetable dataset.

        Args:
            dataset_id: The id of the timetable data set.

        Returns:
            timetable: A Timetable object with the data set details.
        """

        url = self.timetable_endpoint + f"{dataset_id}/"
        response = self._make_request(url)

        if response.status_code == HTTPStatus.OK:
            results = [Timetable(**response.json())]
            return TimetableResponse(count=1, results=results)

        return APIError(status_code=response.status_code, reason=response.content)

    def get_fares_datasets(
        self,
        params: Optional[FaresParams] = None,
    ) -> Union[FaresResponse, APIError]:
        """
        Fetches the fares data sets currently available in the BODS database.

        This only returns meta data about a fares data set including a url to
        the actual data set.

        Args:
            nocs: A list of National Operator Codes.
            status: Limit data sets with a specific status of published, error, expired,
            inactive.
            bounding_box: Limit data sets to those within the BoundingBox.
            limit: Maximum number of results to return per page.
            offset: Number to offset results by.

        """
        if params is None:
            params = FaresParams()

        params = json.loads(params.json(by_alias=True, exclude_none=True))
        response = self._make_request(self.fares_endpoint, params=params)
        if response.status_code == 200:
            return FaresResponse(**response.json())
        return APIError(status_code=response.status_code, reason=response.content)

    def get_fares_dataset(self, dataset_id: int) -> Union[FaresResponse, APIError]:
        """
        Fetches a single fares data sets currently available in the BODS database.
        """
        url = self.fares_endpoint + f"{dataset_id}/"
        response = self._make_request(url)
        if response.status_code == 200:
            results = [Fares(**response.json())]
            return FaresResponse(count=1, results=results)
        return APIError(status_code=response.status_code, reason=response.content)

    def get_siri_vm_data_feed(
        self,
        params: Optional[SIRIVMParams] = None,
    ) -> Union[bytes, APIError]:
        """
        Returns a SIRI-VM byte string representation of vehicles currently providing an
        Automatic Vehicle Locations in BODS.

        Args:
            bounding_box: Limit vehicles to those within the BoundingBox.
            operator_refs: Limit vehicles to only certain operators.
            line_ref: Limit vehicles to those on a certain line.
            producer_ref: Limit vehicles to created by a certain producer.
            origin_ref: Limit vehicles to those with a certain origin.
            destinaton_ref: Limit vehicles to those heading for a certain destination.
        """

        if params is None:
            params = SIRIVMParams()

        params = json.loads(params.json(by_alias=True, exclude_none=True))
        response = self._make_request(self.siri_vm_endpoint, params=params)
        if response.status_code == HTTPStatus.OK:
            return response.content
        return APIError(status_code=response.status_code, reason=response.content)

    def get_siri_vm_data_feed_by_id(self, feed_id: int) -> Union[bytes, APIError]:
        """
        Returns a SIRI-VM byte string representation of vehicles currently providing an
        Automatic Vehicle Locations in BODS.

        Args:
            bounding_box: Limit vehicles to those within the BoundingBox.
            operator_refs: Limit vehicles to only certain operators.
            line_ref: Limit vehicles to those on a certain line.
            producer_ref: Limit vehicles to created by a certain producer.
            origin_ref: Limit vehicles to those with a certain origin.
            destinaton_ref: Limit vehicles to those heading for a certain destination.
        """
        url = self.siri_vm_endpoint + f"{feed_id}/"
        response = self._make_request(url)
        if response.status_code == HTTPStatus.OK:
            return response.content
        return APIError(status_code=response.status_code, reason=response.content)

    def get_siri_vm_from_archive(self) -> Union[bytes, APIError]:
        """
        Returns a SIRI-VM byte string representation of vehicles currently providing an
        Automatic Vehicle Location from the bulk download file in BODS.
        """
        response = self._make_request(self.siri_vm_zip_endpoint)
        if response.status_code == HTTPStatus.OK:
            with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
                with zf.open("siri.xml") as f:
                    return f.read()
        return APIError(status_code=response.status_code, reason=response.content)

    def get_txc_files(
        self, params: Optional[TxcFileParams] = None
    ) -> Union[TxcFileResponse, APIError]:
        """
        Fetches metadata for the TXC files currently available in the BODS database.

        This only returns metadata about a TXC file including its filename.

        Args:
            noc: A National Operator Code.
            line_name: Limit data sets to those containing the specified LineName.
            limit: Maximum number of results to return per page.
            offset: Number to offset results by.
        """

        if params is None:
            params = TxcFileParams()

        params = json.loads(params.json(by_alias=True, exclude_none=True))
        response = self._make_request(self.txc_files_endpoint, params=params)

        if response.status_code == HTTPStatus.OK:
            return TxcFileResponse(**response.json())
        return APIError(status_code=response.status_code, reason=response.content)
