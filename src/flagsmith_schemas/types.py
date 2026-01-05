from decimal import Decimal
from typing import Literal, TypeAlias

DynamoInt: TypeAlias = Decimal
"""An integer value stored in DynamoDB.

DynamoDB represents all numbers as `Decimal`.
`DynamoInt` indicates that the value should be treated as an integer.
"""

DynamoFloat: TypeAlias = Decimal
"""A float value stored in DynamoDB.

DynamoDB represents all numbers as `Decimal`.
`DynamoFloat` indicates that the value should be treated as a float.
"""

UUIDStr: TypeAlias = str
"""A string representing a UUID."""

DateTimeStr: TypeAlias = str
"""A string representing a date and time in ISO 8601 format."""

FeatureType = Literal["STANDARD", "MULTIVARIATE"]
"""Represents the type of a Flagsmith feature. Multivariate features include multiple weighted values."""

FeatureValue: TypeAlias = object
"""Represents the value of a Flagsmith feature. Can be stored a boolean, an integer, or a string.

The default (SaaS) maximum length for strings is 20000 characters.
"""

ContextValue: TypeAlias = DynamoInt | DynamoFloat | bool | str
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
