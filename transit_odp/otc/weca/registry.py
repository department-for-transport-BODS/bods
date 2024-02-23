from logging import getLogger
from transit_odp.otc.weca.client import WecaClient, APIResponse


logger = getLogger(__name__)


class Registry:
    def __init__(self) -> None:
        self._client = WecaClient()
        self.services = []
        self.fields = []

    def fetch_all_records(self) -> APIResponse:
        logger.info("Fetching WECA services")
        response = self._client.fetch_weca_services()
        self.services = response.data
        self.fields = response.fields
        logger.info("Total Services found {}".format(len(self.services)))
        return response
