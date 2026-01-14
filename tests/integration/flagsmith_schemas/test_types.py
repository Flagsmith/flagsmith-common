import gzip

import pytest
from pydantic import TypeAdapter, ValidationError

from flagsmith_schemas.types import DynamoFeatureValue, JsonGzipped


def test_dynamo_feature_value__not_int__coerces_to_str() -> None:
    # Given
    type_adapter: TypeAdapter[DynamoFeatureValue] = TypeAdapter(DynamoFeatureValue)

    # When
    result = type_adapter.validate_python(12.34)

    # Then
    assert result == "12.34"


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
    assert gzip.decompress(result) == json_bytes
