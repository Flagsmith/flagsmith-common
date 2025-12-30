import typing

if typing.TYPE_CHECKING:
    from flagsmith_schemas.dynamodb import FeatureState, MultivariateFeatureStateValue


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
    for i, feature_state in enumerate(values, start=1):
        if feature_state["feature"]["id"] in [
            feature_state["feature"]["id"] for feature_state in values[i:]
        ]:
            raise ValueError(
                f"Feature id={feature_state['feature']['id']} cannot have multiple "
                "feature states for a single identity."
            )
    return values
