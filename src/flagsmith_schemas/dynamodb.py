"""
The types in this module describe the Edge API's data model.
They are used to type DynamoDB documents representing Flagsmith entities.

These types can be used with Pydantic for validation and serialization
when `pydantic` is installed.
Otherwise, they serve as documentation for the structure of the data stored in DynamoDB.
"""

from typing import Annotated, Literal

from flag_engine.segments.types import ConditionOperator, RuleType
from typing_extensions import NotRequired, TypedDict

from flagsmith_schemas.constants import PYDANTIC_INSTALLED
from flagsmith_schemas.types import (
    DateTimeStr,
    DynamoContextValue,
    DynamoFeatureValue,
    DynamoFloat,
    DynamoInt,
    FeatureType,
    JsonGzipped,
    UUIDStr,
)

if PYDANTIC_INSTALLED:
    from flagsmith_schemas.pydantic_types import (
        ValidateIdentityFeatureStatesList,
        ValidateMultivariateFeatureValuesList,
    )


class Feature(TypedDict):
    """Represents a Flagsmith feature, defined at project level."""

    id: DynamoInt
    """Unique identifier for the feature in Core."""
    name: str
    """Name of the feature. Must be unique within a project."""
    type: FeatureType


class MultivariateFeatureOption(TypedDict):
    """Represents a single multivariate feature option in the Flagsmith UI."""

    id: NotRequired[DynamoInt | None]
    """Unique identifier for the multivariate feature option in Core. This is used by Core UI to display the selected option for an identity override for a multivariate feature."""
    value: DynamoFeatureValue
    """The feature state value that should be served when this option's parent multivariate feature state is selected by the engine."""


class MultivariateFeatureStateValue(TypedDict):
    """Represents a multivariate feature state value.

    Identity overrides are meant to hold only one of these, solely to inform the UI which option is selected for the given identity.
    """

    id: NotRequired[DynamoInt | None]
    """Unique identifier for the multivariate feature state value in Core. Used for multivariate bucketing. If feature state created via `edge-identities` APIs in Core, this can be missing or `None`."""
    mv_fs_value_uuid: NotRequired[UUIDStr]
    """The UUID for this multivariate feature state value. Should be used for multivariate bucketing if `id` is `None`."""
    percentage_allocation: DynamoFloat
    """The percentage allocation for this multivariate feature state value. Should be between or equal to 0 and 100."""
    multivariate_feature_option: MultivariateFeatureOption
    """The multivariate feature option that this value corresponds to."""


class FeatureSegment(TypedDict):
    """Represents data specific to a segment feature override."""

    priority: NotRequired[DynamoInt | None]
    """The priority of this segment feature override. Lower numbers indicate stronger priority. If `None` or not set, the weakest priority is assumed."""


class FeatureState(TypedDict):
    """Used to define the state of a feature for an environment, segment overrides, and identity overrides."""

    feature: Feature
    """The feature that this feature state is for."""
    enabled: bool
    """Whether the feature is enabled or disabled."""
    feature_state_value: DynamoFeatureValue
    """The value for this feature state."""
    django_id: NotRequired[DynamoInt | None]
    """Unique identifier for the feature state in Core. If feature state created via Core's `edge-identities` APIs in Core, this can be missing or `None`."""
    featurestate_uuid: NotRequired[UUIDStr]
    """The UUID for this feature state. Should be used if `django_id` is `None`. If not set, should be generated."""
    feature_segment: NotRequired[FeatureSegment | None]
    """Segment override data, if this feature state is for a segment override."""
    multivariate_feature_state_values: "NotRequired[Annotated[list[MultivariateFeatureStateValue], ValidateMultivariateFeatureValuesList]]"
    """List of multivariate feature state values, if this feature state is for a multivariate feature.

    Total `percentage_allocation` sum of the child multivariate feature state values must be less or equal to 100.
    """


class Trait(TypedDict):
    """Represents a key-value pair associated with an identity."""

    trait_key: str
    """Trait key."""
    trait_value: DynamoContextValue
    """Trait value."""


class SegmentCondition(TypedDict):
    """Represents a condition within a segment rule used by Flagsmith engine."""

    operator: ConditionOperator
    """Operator to be applied for this condition."""
    value: NotRequired[str | None]
    """Value to be compared against in this condition. May be `None` for `IS_SET` and `IS_NOT_SET` operators."""
    property_: NotRequired[str | None]
    """The property (context key) this condition applies to. May be `None` for the `PERCENTAGE_SPLIT` operator.

    Named `property_` to avoid conflict with Python's `property` built-in.
    """


class SegmentRule(TypedDict):
    """Represents a rule within a segment used by Flagsmith engine."""

    type: RuleType
    """Type of the rule, defining how conditions are evaluated."""
    rules: "list[SegmentRule]"
    """Nested rules within this rule."""
    conditions: list[SegmentCondition]
    """Conditions that must be met for this rule, evaluated based on the rule type."""


class Segment(TypedDict):
    """Represents a Flagsmith segment. Carries rules, feature overrides, and segment rules."""

    id: DynamoInt
    """Unique identifier for the segment in Core."""
    name: str
    """Name of the segment."""
    rules: list[SegmentRule]
    """List of rules within the segment."""
    feature_states: NotRequired[list[FeatureState]]
    """List of segment overrides."""


class Organisation(TypedDict):
    """Represents data about a Flagsmith organisation. Carries settings necessary for an SDK API operation."""

    id: DynamoInt
    """Unique identifier for the organisation in Core."""
    name: str
    """Organisation name."""
    feature_analytics: NotRequired[bool]
    """Whether the SDK API should log feature analytics events for this organisation. Defaults to `False`."""
    stop_serving_flags: NotRequired[bool]
    """Whether flag serving is disabled for this organisation. Defaults to `False`."""
    persist_trait_data: NotRequired[bool]
    """If set to `False`, trait data will never be persisted for this organisation. Defaults to `True`."""


class Project(TypedDict):
    """Represents data about a Flagsmith project. Carries settings necessary for an SDK API operation."""

    id: DynamoInt
    """Unique identifier for the project in Core."""
    name: str
    """Project name."""
    organisation: Organisation
    """The organisation that this project belongs to."""
    segments: list[Segment]
    """List of segments."""
    server_key_only_feature_ids: NotRequired[list[DynamoInt]]
    """List of feature IDs that are skipped when the SDK API serves flags for a public client-side key."""
    enable_realtime_updates: NotRequired[bool]
    """Whether the SDK API should use real-time updates. Defaults to `False`. Not currently used neither by SDK APIs nor by SDKs themselves."""
    hide_disabled_flags: NotRequired[bool | None]
    """Whether the SDK API should hide disabled flags for this project. Defaults to `False`."""


class Integration(TypedDict):
    """Represents evaluation integration data."""

    api_key: NotRequired[str | None]
    """API key for the integration."""
    base_url: NotRequired[str | None]
    """Base URL for the integration."""


class DynatraceIntegration(Integration):
    """Represents Dynatrace evaluation integration data."""

    entity_selector: str
    """A Dynatrace entity selector string."""


class Webhook(TypedDict):
    """Represents a webhook configuration."""

    url: str
    """Webhook target URL."""
    secret: str
    """Secret used to sign webhook payloads."""


class _EnvironmentBaseFields(TypedDict):
    """Common fields for Environment documents."""

    name: NotRequired[str]
    """Environment name. Defaults to an empty string if not set."""
    updated_at: NotRequired[DateTimeStr | None]
    """Last updated timestamp. If not set, current timestamp should be assumed."""

    allow_client_traits: NotRequired[bool]
    """Whether the SDK API should allow clients to set traits for this environment. Identical to project-level's `persist_trait_data` setting. Defaults to `True`."""
    hide_sensitive_data: NotRequired[bool]
    """Whether the SDK API should hide sensitive data for this environment. Defaults to `False`."""
    hide_disabled_flags: NotRequired[bool | None]
    """Whether the SDK API should hide disabled flags for this environment. If `None`, the SDK API should fall back to project-level setting."""
    use_identity_composite_key_for_hashing: NotRequired[bool]
    """Whether the SDK API should set `$.identity.key` in engine evaluation context to identity's composite key. Defaults to `False`."""
    use_identity_overrides_in_local_eval: NotRequired[bool]
    """Whether the SDK API should return identity overrides as part of the environment document. Defaults to `False`."""

    amplitude_config: NotRequired[Integration | None]
    """Amplitude integration configuration."""
    dynatrace_config: NotRequired[DynatraceIntegration | None]
    """Dynatrace integration configuration."""
    heap_config: NotRequired[Integration | None]
    """Heap integration configuration."""
    mixpanel_config: NotRequired[Integration | None]
    """Mixpanel integration configuration."""
    rudderstack_config: NotRequired[Integration | None]
    """RudderStack integration configuration."""
    segment_config: NotRequired[Integration | None]
    """Segment integration configuration."""
    webhook_config: NotRequired[Webhook | None]
    """Webhook configuration."""


class _EnvironmentV1Fields(TypedDict):
    """Common fields for environment documents in `flagsmith_environments`."""

    api_key: str
    """Public client-side API key for the environment. **INDEXED**."""
    id: DynamoInt
    """Unique identifier for the environment in Core."""


class _EnvironmentV2MetaFields(TypedDict):
    """Common fields for environment documents in `flagsmith_environments_v2`."""

    environment_id: str
    """Unique identifier for the environment in Core. Same as `Environment.id`, but string-typed to reduce coupling with Core's type definitions **INDEXED**."""
    environment_api_key: str
    """Public client-side API key for the environment. **INDEXED**."""
    document_key: Literal["_META"]
    """The fixed document key for the environment v2 document. Always `"_META"`. **INDEXED**."""

    id: DynamoInt
    """Unique identifier for the environment in Core. Exists for compatibility with the API environment document schema."""


class _EnvironmentBaseFieldsUncompressed(TypedDict):
    """Common fields for uncompressed environment documents."""

    project: Project
    """Project-specific data for this environment."""
    feature_states: list[FeatureState]
    """List of feature states representing the environment defaults."""
    compressed: NotRequired[Literal[False]]
    """Either `False` or absent to indicate the data is uncompressed."""


class _EnvironmentBaseFieldsCompressed(TypedDict):
    """Common fields for compressed environment documents."""

    project: JsonGzipped[Project]
    """Project-specific data for this environment. **COMPRESSED**."""
    feature_states: JsonGzipped[list[FeatureState]]
    """List of feature states representing the environment defaults. **COMPRESSED**."""
    compressed: Literal[True]
    """Always `True` to indicate the data is compressed."""


### Root document schemas below. Indexed fields are marked as **INDEXED** in the docstrings. Compressed fields are marked as **COMPRESSED**. ###


class EnvironmentAPIKey(TypedDict):
    """Represents a server-side API key for a Flagsmith environment.

    **DynamoDB table**: `flagsmith_environment_api_key`
    """

    id: DynamoInt
    """Unique identifier for the environment API key in Core. **INDEXED**."""
    key: str
    """The server-side API key string, e.g. `"ser.xxxxxxxxxxxxx"`. **INDEXED**."""
    created_at: DateTimeStr
    """Creation timestamp."""
    name: str
    """Name of the API key."""
    client_api_key: str
    """The corresponding public client-side API key."""
    expires_at: NotRequired[DateTimeStr | None]
    """Expiration timestamp. If `None`, the key does not expire."""
    active: bool
    """Whether the key is active. Defaults to `True`."""


class Identity(TypedDict):
    """Represents a Flagsmith identity within an environment. Carries traits and feature overrides.
    Used for per-identity flag evaluations in remote evaluation mode.

    **DynamoDB table**: `flagsmith_identities`
    """

    identifier: str
    """Unique identifier for the identity. **INDEXED**."""
    environment_api_key: str
    """API key of the environment this identity belongs to. Used to scope the identity within a specific environment. **INDEXED**."""
    identity_uuid: UUIDStr
    """The UUID for this identity. **INDEXED**."""
    composite_key: str
    """A composite key combining the environment and identifier. **INDEXED**.

    Generated as: `{environment_api_key}_{identifier}`.
    """
    created_date: DateTimeStr
    """Creation timestamp."""
    identity_features: (
        "NotRequired[Annotated[list[FeatureState], ValidateIdentityFeatureStatesList]]"
    )
    """List of identity overrides for this identity."""
    identity_traits: list[Trait]
    """List of traits associated with this identity."""
    django_id: NotRequired[DynamoInt | None]
    """Unique identifier for the identity in Core. If identity created via Core's `edge-identities` API, this can be missing or `None`."""


class Environment(
    _EnvironmentBaseFieldsUncompressed,
    _EnvironmentV1Fields,
    _EnvironmentBaseFields,
):
    """Represents a Flagsmith environment. Carries all necessary data for flag evaluation within the environment.

    **DynamoDB table**: `flagsmith_environments`
    """


class EnvironmentCompressed(
    _EnvironmentBaseFieldsCompressed,
    _EnvironmentV1Fields,
    _EnvironmentBaseFields,
):
    """Represents a Flagsmith environment. Carries all necessary data for flag evaluation within the environment.
    Has compressed fields.

    **DynamoDB table**: `flagsmith_environments`
    """


class EnvironmentV2Meta(
    _EnvironmentBaseFieldsUncompressed,
    _EnvironmentV2MetaFields,
    _EnvironmentBaseFields,
):
    """Represents a Flagsmith environment. Carries all necessary data for flag evaluation within the environment.

    **DynamoDB table**: `flagsmith_environments_v2`
    """


class EnvironmentV2MetaCompressed(
    _EnvironmentBaseFieldsCompressed,
    _EnvironmentV2MetaFields,
    _EnvironmentBaseFields,
):
    """Represents a Flagsmith environment. Carries all necessary data for flag evaluation within the environment.
    Has compressed fields.

    **DynamoDB table**: `flagsmith_environments_v2`
    """


class EnvironmentV2IdentityOverride(TypedDict):
    """Represents an identity override.
    Used for per-identity flag evaluations in local evaluation mode. Presented as part of the API environment document.

    **DynamoDB table**: `flagsmith_environments_v2`
    """

    environment_id: str
    """Unique identifier for the environment in Core. **INDEXED**."""
    document_key: str
    """The document key for this identity override, formatted as `identity_override:{feature Core ID}:{identity UUID}`. **INDEXED**."""
    environment_api_key: str
    """Public client-side API key for the environment. **INDEXED**."""
    identifier: str
    """Unique identifier for the identity. **INDEXED**."""
    identity_uuid: str
    """The UUID for this identity, used by `edge-identities` APIs in Core. **INDEXED**."""
    feature_state: FeatureState
    """The feature state override for this identity."""
