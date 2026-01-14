"""
The types in this module describe Flagsmith SDK API request and response schemas.
The docstrings here comprise user-facing documentation for these types.

The types are used by:
 - SDK API OpenAPI schema generation.
 - Flagsmith's API and SDK implementations written in Python.

These types can be used with for validation and serialization
with any library that supports TypedDict, such as Pydantic or typeguard.

When updating this module, ensure that the changes are backwards compatible.
"""

from flag_engine.engine import ContextValue
from flag_engine.segments.types import ConditionOperator, RuleType
from typing_extensions import NotRequired, TypedDict

from flagsmith_schemas.types import FeatureType, FeatureValue, UUIDStr


class Feature(TypedDict):
    """Represents a Flagsmith feature, defined at project level."""

    id: int
    """Unique identifier for the feature in Core."""
    name: str
    """Name of the feature. Must be unique within a project."""
    type: FeatureType
    """Feature type."""


class MultivariateFeatureOption(TypedDict):
    """Represents a single multivariate feature option in the Flagsmith UI."""

    value: str
    """The feature state value that should be served when this option's parent multivariate feature state is selected by the engine."""


class MultivariateFeatureStateValue(TypedDict):
    """Represents a multivariate feature state value."""

    id: int | None
    """Unique identifier for the multivariate feature state value in Core. Used for multivariate bucketing. If feature state created via `edge-identities` APIs in Core, this can be missing or `None`."""
    mv_fs_value_uuid: UUIDStr | None
    """The UUID for this multivariate feature state value. Should be used for multivariate bucketing if `id` is null."""
    percentage_allocation: float
    """The percentage allocation for this multivariate feature state value. Should be between or equal to 0 and 100; total percentage allocation of grouped `MultivariateFeatureStateValue` must not exceed 100."""
    multivariate_feature_option: MultivariateFeatureOption
    """The multivariate feature option that this value corresponds to."""


class FeatureSegment(TypedDict):
    """Represents data specific to a segment feature override."""

    priority: int | None
    """The priority of this segment feature override. Lower numbers indicate stronger priority. If null or not set, the weakest priority is assumed."""


class FeatureState(TypedDict):
    """Used to define the state of a feature for an environment, segment overrides, and identity overrides."""

    feature: Feature
    """The feature that this feature state is for."""
    enabled: bool
    """Whether the feature is enabled or disabled."""
    feature_state_value: FeatureValue
    """The value for this feature state."""
    featurestate_uuid: UUIDStr
    """The UUID for this feature state."""
    feature_segment: FeatureSegment | None
    """Segment override data, if this feature state is for a segment override."""
    multivariate_feature_state_values: list[MultivariateFeatureStateValue]
    """List of multivariate feature state values, if this feature state is for a multivariate feature."""


class Trait(TypedDict):
    """Represents a key-value pair associated with an identity."""

    trait_key: str
    """Key of the trait."""
    trait_value: ContextValue
    """Value of the trait."""


class SegmentCondition(TypedDict):
    """Represents a condition within a segment rule used by Flagsmith engine."""

    operator: ConditionOperator
    """Operator to be applied for this condition."""
    value: str
    """Value to be compared against in this condition. May be `None` for `IS_SET` and `IS_NOT_SET` operators."""
    property_: str
    """The property (context key) this condition applies to. May be `None` for the `PERCENTAGE_SPLIT` operator.

    Named `property_` for legacy reasons.
    """


class SegmentRule(TypedDict):
    """Represents a rule within a segment used by Flagsmith engine. Root rules usually contain nested rules."""

    type: RuleType
    """Type of the rule, defining how conditions are evaluated."""
    rules: "list[SegmentRule]"
    """Nested rules within this rule."""
    conditions: list[SegmentCondition]
    """Conditions that must be met for this rule, evaluated based on the rule type."""


class Segment(TypedDict):
    """Represents a Flagsmith segment. Carries rules and feature overrides."""

    id: int
    """Unique identifier for the segment in Core."""
    name: str
    """Segment name."""
    rules: list[SegmentRule]
    """List of rules within the segment."""
    feature_states: NotRequired[list[FeatureState]]
    """List of segment overrides."""


class Project(TypedDict):
    """Represents a Flagsmith project. For SDKs, this is mainly used to convey segment data."""

    segments: list[Segment]
    """List of segments."""


class IdentityOverride(TypedDict):
    """Represents an identity override, defining feature states specific to an identity."""

    identifier: str
    """Unique identifier for the identity."""
    identity_features: list[FeatureState]
    """List of identity overrides for this identity."""


class TraitInput(TypedDict):
    """Represents a key-value pair trait provided as input when creating or updating an identity."""

    trait_key: str
    """Trait key."""
    trait_value: ContextValue
    """Trait value. If `null`, the trait will be deleted."""
    transient: NotRequired[bool | None]
    """Whether this trait is transient (not persisted). Defaults to `false`."""


class V1Flag(TypedDict):
    """Represents a single flag (feature state) returned by the Flagsmith SDK."""

    feature: Feature
    """The feature that this flag represents."""
    enabled: bool
    """Whether the feature is enabled or disabled."""
    feature_state_value: FeatureValue
    """The value for this feature state."""


### Root request schemas below. ###


class V1IdentitiesRequest(TypedDict):
    """`/api/v1/identities/` request.

    Used to retrieve flags for an identity and store its traits.
    """

    identifier: str
    """Unique identifier for the identity."""
    traits: NotRequired[list[TraitInput] | None]
    """List of traits to set for the identity. If `null` or not provided, no traits are set or updated."""
    transient: NotRequired[bool | None]
    """Whether the identity is transient (not persisted). Defaults to `false`."""


### Root response schemas below. ###


class V1EnvironmentDocumentResponse(TypedDict):
    """`/api/v1/environment-documents/` response.

    Powers Flagsmith SDK's local evaluation mode.
    """

    api_key: str
    """Public client-side API key for the environment, used to identify it."""
    feature_states: list[FeatureState]
    """List of feature states representing the environment defaults."""
    identity_overrides: list[IdentityOverride]
    """List of identity overrides defined for this environment."""
    name: str
    """Environment name."""
    project: Project
    """Project-specific data for this environment."""


V1FlagsResponse = list[V1Flag]
"""`/api/v1/flags/` response.

A list of flags for the specified environment."""


class V1IdentitiesResponse(TypedDict):
    """`/api/v1/identities/` response.

    Represents the identity created or updated, along with its flags.
    """

    identifier: str
    """Unique identifier for the identity."""
    flags: list[V1Flag]
    """List of flags (feature states) for the identity."""
    traits: list[Trait]
    """List of traits associated with the identity."""
