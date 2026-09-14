from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from flagsmith_schemas.api import FeatureState, V1Flag


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


@pytest.mark.parametrize(
    "schema_type",
    [FeatureState, V1Flag],
)
def test_type_adapter__metadata__preserved_verbatim(
    schema_type: type[FeatureState] | type[V1Flag],
    feature_state_metadata: dict[str, Any],
) -> None:
    # Given
    type_adapter = TypeAdapter(schema_type)
    data = {
        "feature": {"id": 1, "name": "feature", "type": "STANDARD"},
        "enabled": True,
        "feature_state_value": "value",
        "featurestate_uuid": "652d8931-37d9-438e-9825-f525b9e83077",
        "feature_segment": None,
        "multivariate_feature_state_values": [],
        "metadata": feature_state_metadata,
    }

    # When
    document = type_adapter.validate_python(data)

    # Then
    # Known keys are validated, unknown keys are preserved as-is
    assert document["metadata"] == feature_state_metadata


@pytest.mark.parametrize(
    "schema_type",
    [FeatureState, V1Flag],
)
def test_type_adapter__no_metadata__key_absent(
    schema_type: type[FeatureState] | type[V1Flag],
) -> None:
    # Given
    type_adapter = TypeAdapter(schema_type)
    data = {
        "feature": {"id": 1, "name": "feature", "type": "STANDARD"},
        "enabled": True,
        "feature_state_value": "value",
        "featurestate_uuid": "652d8931-37d9-438e-9825-f525b9e83077",
        "feature_segment": None,
        "multivariate_feature_state_values": [],
    }

    # When
    document = type_adapter.validate_python(data)

    # Then
    assert "metadata" not in document


@pytest.mark.parametrize(
    ("invalid_experiment_field", "invalid_value"),
    [
        ("id", "not-an-int"),
        ("in_experiment", "not-a-bool"),
    ],
)
def test_type_adapter__invalid_experiment_metadata__raises_expected(
    invalid_experiment_field: str,
    invalid_value: Any,
    feature_state_metadata: dict[str, Any],
) -> None:
    # Given
    type_adapter = TypeAdapter(V1Flag)
    feature_state_metadata["experiment"][invalid_experiment_field] = invalid_value
    data = {
        "feature": {"id": 1, "name": "feature", "type": "STANDARD"},
        "enabled": True,
        "feature_state_value": "value",
        "metadata": feature_state_metadata,
    }

    # When
    with pytest.raises(ValidationError) as exc_info:
        type_adapter.validate_python(data)

    # Then
    assert [error["loc"] for error in exc_info.value.errors()] == [
        ("metadata", "experiment", invalid_experiment_field)
    ]
