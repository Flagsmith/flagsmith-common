from typing import TypedDict, Any, NotRequired, Protocol
from django.contrib.contenttypes.models import ContentType

class HasId(Protocol):
    id: int 

class MetadataItem(TypedDict, total=False):
    model_field: HasId
    field_value: Any
    delete: NotRequired[bool]
