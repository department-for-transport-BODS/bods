from dataclasses import dataclass

from typing import Dict, Final, Optional

from transit_odp.data_quality import models
from transit_odp.dqs.constants import Level, Category, CheckBasis


@dataclass
class Observation:
    level: Level
    category: Category
    title: str
    text: str
    list_url_name: str
    model: Optional[models.DataQualityWarningBase]
    extra_info: Optional[Dict[str, str]] = None
    impacts: str = None
    weighting: float = None
    check_basis: CheckBasis = None
    resolve: str = None
    preamble: str = None
    is_active: bool = True

    @property
    def type(self):
        return self.category.value
