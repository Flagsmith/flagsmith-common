from pydantic import TypeAdapter

from flagsmith_schemas.types import DynamoFeatureValue


def test_dynamo_feature_value__not_int__coerces_to_str() -> None:
    # Given
    type_adapter: TypeAdapter[DynamoFeatureValue] = TypeAdapter(DynamoFeatureValue)

    # When
    result = type_adapter.validate_python(12.34)

    # Then
    assert result == "12.34"
