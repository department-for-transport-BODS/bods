import logging
from typing import Iterator, List, Union

import pandas as pd
from django.db.models import QuerySet

from transit_odp.organisation.models import DatasetRevision
from transit_odp.transmodel.models import Service, ServiceLink, ServicePattern

from .dataframes import (
    create_naptan_locality_df,
    create_naptan_stoppoint_df,
    create_naptan_stoppoint_df_from_queryset,
    create_service_df,
    create_service_df_from_queryset,
    create_service_link_df,
    create_service_link_df_from_queryset,
    df_to_service_links,
    df_to_service_pattern_service,
    df_to_service_patterns,
    df_to_services,
    get_first_and_last_expiration_dates,
)

logger = logging.getLogger(__name__)


class ETLUtility(object):
    """
    WARNING - CM - 09/10/2020
    This class has no reason to exist it's basically a collection of pandas utility
    functions. I've extracted the functionality into a module of functions
    unfortunately several parts of the transxchange pipeline depend on this class so
    I've just proxied the extracted functionality as not to break the API of
    this class.
    """

    @classmethod
    def create_hash(cls, s: pd.Series):
        """Hash together values in pd.Series"""
        return hash(tuple(s))

    @classmethod
    def df_to_services(
        cls, revision: DatasetRevision, df: pd.DataFrame
    ) -> Iterator[Service]:
        return df_to_services(revision, df)

    @classmethod
    def df_to_service_links(cls, df: pd.DataFrame) -> Iterator[ServiceLink]:
        return df_to_service_links(df)

    @classmethod
    def df_to_service_pattern_service(
        cls, df: pd.DataFrame
    ) -> Iterator[ServicePattern.service_links.through]:
        return df_to_service_pattern_service(df)

    @classmethod
    def df_to_service_patterns(
        cls, revision: DatasetRevision, df: pd.DataFrame
    ) -> Iterator[ServicePattern]:
        return df_to_service_patterns(revision, df)

    @classmethod
    def get_first_and_last_expiration_dates(
        cls, expiration_dates: list, start_dates: list
    ):
        return get_first_and_last_expiration_dates(expiration_dates, start_dates)

    @classmethod
    def create_naptan_stoppoint_df_from_queryset(cls, qs: QuerySet):
        return create_naptan_stoppoint_df_from_queryset(qs)

    @classmethod
    def create_naptan_stoppoint_df(cls, data=None):
        return create_naptan_stoppoint_df(data)

    @classmethod
    def create_naptan_locality_df(cls, data=None):
        return create_naptan_locality_df(data)

    @classmethod
    def create_service_link_df(cls, data=None):
        return create_service_link_df(data)

    @classmethod
    def create_service_link_df_from_queryset(
        cls, qs: Union[QuerySet, List[ServiceLink]]
    ):
        return create_service_link_df_from_queryset(qs)

    @classmethod
    def create_service_df(cls, data=None):
        return create_service_df(data)

    @classmethod
    def create_service_df_from_queryset(cls, qs: Union[QuerySet, List[Service]]):
        return create_service_df_from_queryset(qs)
