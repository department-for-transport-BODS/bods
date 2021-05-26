from typing import Generic, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")


class Id(GenericModel, Generic[T]):
    id: T

    class Config:
        # identity Value Object must be immutable
        allow_mutation = False
