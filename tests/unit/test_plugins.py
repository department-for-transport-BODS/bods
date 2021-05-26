import pytest

from transit_odp.bods.adapters.gateways.cavl import CAVLService
from transit_odp.bods.interfaces.plugins import get_cavl_service


class TestGetCavlService:
    def test_service_returned(self, settings):
        # Setup
        # ensure settings.CAVL_SERVICE is pointing to service
        settings.CAVL_SERVICE = "transit_odp.bods.adapters.gateways.cavl.CAVLService"

        # Test
        cavl_service = get_cavl_service()

        # Assert
        assert isinstance(cavl_service, CAVLService)

    def test_error_raised_when_incorrect_path_given(self, settings):
        # Setup
        # ensure settings.CAVL_SERVICE points to incorrect location
        settings.CAVL_SERVICE = "transit_odp.to.somewhere.that.doesnt.exist.CAVLService"

        # Test
        with pytest.raises(ImportError):
            get_cavl_service()
