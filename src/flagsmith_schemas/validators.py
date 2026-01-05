import typing
from decimal import Decimal

from flagsmith_schemas.constants import MAX_STRING_FEATURE_STATE_VALUE_LENGTH

if typing.TYPE_CHECKING:
    from flagsmith_schemas.dynamodb import FeatureState, MultivariateFeatureStateValue
    from flagsmith_schemas.types import DynamoFeatureValue


def validate_dynamo_feature_state_value(
    value: typing.Any,
) -> "DynamoFeatureValue":
    if isinstance(value, bool | None):
        return value
    if isinstance(value, str):
        if len(value) > MAX_STRING_FEATURE_STATE_VALUE_LENGTH:
            raise ValueError(
                "Dynamo feature state value string length cannot exceed "
                f"{MAX_STRING_FEATURE_STATE_VALUE_LENGTH} characters "
                f"(got {len(value)} characters)."
            )
        return value
    if isinstance(value, int):
        return Decimal(value)
    return str(value)


def validate_multivariate_feature_state_values(
    values: "list[MultivariateFeatureStateValue]",
) -> "list[MultivariateFeatureStateValue]":
    total_percentage = sum(value["percentage_allocation"] for value in values)
    if total_percentage > 100:
        raise ValueError(
            "Total `percentage_allocation` of multivariate feature state values "
            "cannot exceed 100."
        )
    return values


def validate_identity_feature_states(
    values: "list[FeatureState]",
) -> "list[FeatureState]":
    seen: set[Decimal] = set()

    for feature_state in values:
        feature_id = feature_state["feature"]["id"]
        if feature_id in seen:
            raise ValueError(
                f"Feature id={feature_id} cannot have multiple "
                "feature states for a single identity."
            )
        seen.add(feature_id)

    return values
