from pydantic import TypeAdapter

from flagsmith_schemas.api import FeatureState


def test_feature_state__featurestate_uuid__expected_json_schema() -> None:
    # Given
    type_adapter: TypeAdapter[FeatureState] = TypeAdapter(FeatureState)

    # When
    schema = type_adapter.json_schema()["properties"]["featurestate_uuid"]

    # Then
    assert schema == {
        "format": "uuid",
        "title": "Featurestate Uuid",
        "type": "string",
    }
