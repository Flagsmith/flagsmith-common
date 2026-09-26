import gzip
from decimal import Decimal

import pytest
from pydantic import TypeAdapter, ValidationError

from flagsmith_schemas.types import (
    DynamoContextValue,
    DynamoFeatureValue,
    DynamoInt,
    JsonGzipped,
)


def test_dynamo_feature_value__not_int__coerces_to_str() -> None:
    # Given
    type_adapter: TypeAdapter[DynamoFeatureValue] = TypeAdapter(DynamoFeatureValue)

    # When
    result = type_adapter.validate_python(12.34)

    # Then
    assert result == "12.34"


@pytest.mark.parametrize(
    ("value", "expected_result"),
    [
        pytest.param(Decimal("1234"), Decimal("1234"), id="integer"),
        pytest.param(Decimal("12.34"), "12.34", id="non_integer"),
    ],
)
def test_dynamo_feature_value__stored_decimal__returns_expected(
    value: Decimal,
    expected_result: DynamoFeatureValue,
) -> None:
    # Given
    type_adapter: TypeAdapter[DynamoFeatureValue] = TypeAdapter(DynamoFeatureValue)

    # When
    result = type_adapter.validate_python(value)

    # Then
    assert result == expected_result


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(Decimal("42"), id="integer"),
        pytest.param(Decimal("1.5"), id="non_integer"),
    ],
)
def test_dynamo_context_value__stored_decimal__returns_unchanged(
    value: Decimal,
) -> None:
    # Given
    type_adapter: TypeAdapter[DynamoContextValue] = TypeAdapter(DynamoContextValue)

    # When
    result = type_adapter.validate_python(value)

    # Then
    assert str(result) == str(value)


def test_dynamo_int__stored_non_integer_decimal__raises_expected() -> None:
    # Given
    type_adapter: TypeAdapter[DynamoInt] = TypeAdapter(DynamoInt)

    # When
    with pytest.raises(ValidationError) as exc_info:
        type_adapter.validate_python(Decimal("1.5"))

    # Then
    assert exc_info.value.errors()[0]["type"] == "int_from_float"


def test_dynamo_feature_value__long_string__raises_expected() -> None:
    # Given
    type_adapter: TypeAdapter[DynamoFeatureValue] = TypeAdapter(DynamoFeatureValue)

    # When
    with pytest.raises(ValidationError) as exc_info:
        type_adapter.validate_python("a" * 20_001)

    # Then
    assert len(exc_info.value.errors()) == 1
    assert (
        exc_info.value.errors()[0].items()
        >= {
            "type": "value_error",
            "msg": "Value error, Dynamo feature state value string length cannot exceed 20000 characters (got 20001 characters).",
        }.items()
    )


def test_json_gzipped__valid_json_bytes__accepts_expected() -> None:
    # Given
    type_adapter: TypeAdapter[JsonGzipped[dict[str, int]]] = TypeAdapter(
        JsonGzipped[dict[str, int]]
    )
    input_data: dict[str, int] = {"key": 123}
    json_bytes = b'{"key":123}'

    # When
    result = type_adapter.validate_python(input_data)

    # Then
    assert gzip.decompress(bytes(result)) == json_bytes
