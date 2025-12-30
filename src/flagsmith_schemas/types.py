from decimal import Decimal
from typing import TYPE_CHECKING, Annotated, Literal, TypeAlias

from flagsmith_schemas.constants import PYDANTIC_INSTALLED

if PYDANTIC_INSTALLED:
    from flagsmith_schemas.pydantic_types import (
        ValidateDecimalAsFloat,
        ValidateDecimalAsInt,
        ValidateDynamoFeatureStateValue,
        ValidateStrAsISODateTime,
        ValidateStrAsUUID,
    )
elif not TYPE_CHECKING:
    # This code runs at runtime when Pydantic is not installed.
    # We could use PEP 649 strings with `Annotated`, but Pydantic is inconsistent in how it parses them.
    # Define dummy types instead.
    ValidateDecimalAsFloat = ...
    ValidateDecimalAsInt = ...
    ValidateDynamoFeatureStateValue = ...
    ValidateStrAsISODateTime = ...
    ValidateStrAsUUID = ...


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

UUIDStr: TypeAlias = Annotated[str, ValidateStrAsUUID]
"""A string representing a UUID."""

DateTimeStr: TypeAlias = Annotated[str, ValidateStrAsISODateTime]
"""A string representing a date and time in ISO 8601 format."""

FeatureType = Literal["STANDARD", "MULTIVARIATE"]
"""Represents the type of a Flagsmith feature. Multivariate features include multiple weighted values."""

DynamoFeatureValue: TypeAlias = Annotated[
    DynamoInt | bool | str | None,
    ValidateDynamoFeatureStateValue,
]
"""Represents the value of a Flagsmith feature. Can be stored a boolean, an integer, or a string.

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

ConditionOperator = Literal[
    "EQUAL",
    "GREATER_THAN",
    "LESS_THAN",
    "LESS_THAN_INCLUSIVE",
    "CONTAINS",
    "GREATER_THAN_INCLUSIVE",
    "NOT_CONTAINS",
    "NOT_EQUAL",
    "REGEX",
    "PERCENTAGE_SPLIT",
    "MODULO",
    "IS_SET",
    "IS_NOT_SET",
    "IN",
]
"""Represents segment condition operators used by Flagsmith engine."""

RuleType = Literal[
    "ALL",
    "ANY",
    "NONE",
]
"""Represents segment rule types used by Flagsmith engine."""
