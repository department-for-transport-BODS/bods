from typing import List

from pydantic.fields import Field

from .base import BaseAPIParams, BaseAPIResponse, BaseDataset, BoundingBoxMixin


class Fares(BaseDataset):
    num_of_lines: int = Field(alias="numOfLines")
    num_of_fare_zones: int = Field(alias="numOfFareZones")
    num_of_sales_offer_packages: int = Field(alias="numOfSalesOfferPackages")
    num_of_fare_products: int = Field(alias="numOfFareProducts")
    num_of_user_types: int = Field(alias="numOfUserTypes")


class FaresResponse(BaseAPIResponse):
    results: List[Fares]


class FaresParams(BaseAPIParams, BoundingBoxMixin):
    class Config(BaseAPIParams.Config):
        pass
