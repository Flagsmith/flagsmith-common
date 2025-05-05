from typing import Any, NotRequired, Protocol, TypedDict


class HasId(Protocol):
    id: int


class MetadataItem(TypedDict, total=False):
    model_field: HasId
    field_value: Any
    delete: NotRequired[bool]
