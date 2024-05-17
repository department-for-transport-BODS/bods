from django.db import models
from django.db.models import F
from transit_odp.dqs.constants import STATUSES


class TaskResultsQueryset(models.QuerySet):
    """
    This queryset class is to include all querysets related to the TaskResults model
    """

    def get_valid_taskresults(self, txcfileattributes: list) -> list:
        """Get valid TaskResults objects for the TxCFiles"""
        txcfileattribute_ids = [attr.id for attr in txcfileattributes]
        return self.filter(transmodel_txcfileattributes__id__in=txcfileattribute_ids)
        
    
    def get_pending_objects(self, txcfileattributes: list) -> list:
        """
        Filter for PENDING TaskResults items for the TxCFiles and annotate queue_names from Checks
        """
        include_status = STATUSES["PENDING"]
        qs = self.get_valid_taskresults(txcfileattributes).filter(
            status=include_status
        ).annotate(queue_name=F("checks__queue_name"))
        
        return qs