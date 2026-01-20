from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Generic,
    Literal,
    SupportsBytes,
    TypeAlias,
    TypeVar,
    get_args,
)

from flagsmith_schemas.constants import PYDANTIC_INSTALLED

if PYDANTIC_INSTALLED:
    from pydantic import (
        GetCoreSchemaHandler,
        TypeAdapter,
        WithJsonSchema,
    )
    from pydantic_core import core_schema

    from flagsmith_schemas.pydantic_types import (
        ValidateDecimalAsFloat,
        ValidateDecimalAsInt,
        ValidateDynamoFeatureStateValue,
        ValidateStrAsISODateTime,
        ValidateStrAsUUID,
    )
    from flagsmith_schemas.utils import json_gzip
elif not TYPE_CHECKING:
    # This code runs at runtime when Pydantic is not installed.
    # We could use PEP 649 strings with `Annotated`, but Pydantic is inconsistent in how it parses them.
    # Define dummy types instead.
    def WithJsonSchema(_: object) -> object:
        return ...

    ValidateDecimalAsFloat = ...
    ValidateDecimalAsInt = ...
    ValidateDynamoFeatureStateValue = ...
    ValidateStrAsISODateTime = ...
    ValidateStrAsUUID = ...

T = TypeVar("T")


class DynamoBinary(SupportsBytes):
    """boto3's wrapper type for bytes stored in DynamoDB."""

    value: bytes | bytearray


class JsonGzipped(DynamoBinary, Generic[T]):
    """A gzipped JSON blob representing a value of type `T`."""

    if PYDANTIC_INSTALLED:

        @classmethod
        def __get_pydantic_core_schema__(
            cls,
            source_type: "type[JsonGzipped[T]]",
            handler: GetCoreSchemaHandler,
        ) -> core_schema.CoreSchema:
            _adapter: TypeAdapter[T] = TypeAdapter(get_args(source_type)[0])

            def _validate_json_gzipped(data: Any) -> bytes:
                return json_gzip(_adapter.validate_python(data))

            # We're returning bytes here for two reasons:
            # 1. boto3.dynamodb seems to expect bytes as input for Binary columns.
            # 2. We want to avoid having boto3 as a dependency.
            return core_schema.no_info_before_validator_function(
                _validate_json_gzipped,
                core_schema.bytes_schema(strict=False),
            )


DynamoInt: TypeAlias = Annotated[Decimal, ValidateDecimalAsInt]
"""An integer value stored in DynamoDB.

DynamoDB represents all numbers as `Decimal`.
`DynamoInt` indicates that the value should be treated as an integer.
"""

DynamoFloat: TypeAlias = Annotated[Decimal, ValidateDecimalAsFloat]
"""A float value stored in DynamoDB.

DynamoDB represents all numbers as `Decimal`.
`DynamoFloat` indicates that the value should be treated as a float.
"""

UUIDStr: TypeAlias = Annotated[
    str,
    ValidateStrAsUUID,
    WithJsonSchema({"type": "string", "format": "uuid"}),
]
"""A string representing a UUID."""

DateTimeStr: TypeAlias = Annotated[str, ValidateStrAsISODateTime]
"""A string representing a date and time in ISO 8601 format."""

FeatureType = Literal["STANDARD", "MULTIVARIATE"]
"""Represents the type of a Flagsmith feature. Multivariate features include multiple weighted values."""

DynamoFeatureValue: TypeAlias = Annotated[
    DynamoInt | bool | str | None,
    ValidateDynamoFeatureStateValue,
]
"""Represents the value of a Flagsmith feature stored in DynamoDB. Can be stored a boolean, an integer, or a string.

The default (SaaS) maximum length for strings is 20000 characters.
"""

DynamoContextValue: TypeAlias = DynamoInt | DynamoFloat | bool | str
"""Represents a scalar value in the Flagsmith context, e.g., of an identity trait.
Here's how we store different types:
- Numeric string values (int, float) are stored as numbers.
- Boolean values are stored as booleans.
- All other values are stored as strings.
- Maximum length for strings is 2000 characters.

This type does not include complex structures like lists or dictionaries.
"""

FeatureValue: TypeAlias = int | bool | str | None
"""Represents the value of a Flagsmith feature. Can be stored a boolean, an integer, or a string."""
