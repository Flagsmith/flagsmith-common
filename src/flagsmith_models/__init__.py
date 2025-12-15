"""
Types describing Flagsmith Edge API's data model.
The schemas are written to DynamoDB documents by Core, and read by Edge.
"""

from typing import Literal, TypeAlias

from typing_extensions import NotRequired, TypedDict

from flagsmith_models.types import DateTimeStr, UUIDStr

FeatureType = Literal["STANDARD", "MULTIVARIATE"]
"""Represents the type of a Flagsmith feature. Multivariate features include multiple weighted values."""

FeatureValue: TypeAlias = object
"""Represents the value of a Flagsmith feature. Can be stored a boolean, an integer, or a string.

The default (SaaS) maximum length for strings is 20000 characters.
"""

ContextValue: TypeAlias = int | float | bool | str
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


class Feature(TypedDict):
    """Represents a Flagsmith feature defined at project level."""

    id: int
    """Unique identifier for the feature in Core."""
    name: str
    """Name of the feature. Must be unique within a project."""
    type: FeatureType


class MultivariateFeatureOption(TypedDict):
    """A container for a feature state value of a multivariate feature state."""

    id: NotRequired[int | None]
    """Unique identifier for the multivariate feature option in Core. **DEPRECATED**: MultivariateFeatureValue.id should be used instead."""
    value: FeatureValue
    """The feature state value that should be served when this option's parent multivariate feature state is selected by the engine."""


class MultivariateFeatureStateValue(TypedDict):
    """Represents a multivariate feature state value assigned to an identity or environment."""

    id: NotRequired[int | None]
    """Unique identifier for the multivariate feature state value in Core. TODO: document why and when this can be `None`."""
    mv_fs_value_uuid: NotRequired[UUIDStr]
    """The UUID for this multivariate feature state value. Should be used if `id` is `None`."""
    percentage_allocation: float
    """The percentage allocation for this multivariate feature state value. Should be between or equal to 0 and 100."""
    multivariate_feature_option: MultivariateFeatureOption
    """The multivariate feature option that this value corresponds to."""


class FeatureSegment(TypedDict):
    """Represents data specific to a segment feature override."""

    priority: NotRequired[int | None]
    """The priority of this segment feature override. Lower numbers indicate stronger priority. If `None` or not set, the weakest priority is assumed."""


class FeatureState(TypedDict):
    """Represents a Flagsmith feature state. Used to define the state of a feature for an environment, segment overrides, and identity overrides."""

    feature: Feature
    """The feature that this feature state is for."""
    enabled: bool
    """Whether the feature is enabled or disabled."""
    feature_state_value: FeatureValue
    """The value for this feature state."""
    django_id: NotRequired[int | None]
    """Unique identifier for the feature state in Core. TODO: document why and when this can be `None`."""
    featurestate_uuid: NotRequired[UUIDStr]
    """The UUID for this feature state. Should be used if `django_id` is `None`. If not set, should be generated."""
    feature_segment: NotRequired[FeatureSegment | None]
    """Segment override data, if this feature state is for a segment override."""
    multivariate_feature_state_values: NotRequired[list[MultivariateFeatureStateValue]]
    """List of multivariate feature state values, if this feature state is for a multivariate feature.

    Total `percentage_allocation` sum must be less or equal to 100.
    """


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

    id: int
    """Unique identifier for the segment in Core."""
    name: str
    """Name of the segment."""
    rules: list[SegmentRule]
    """List of rules within the segment."""
    feature_states: list[FeatureState]
    """List of segment overrides."""


class Organisation(TypedDict):
    """Represents data about a Flagsmith organisation. Carries settings necessary for an SDK API operation."""

    id: int
    """Unique identifier for the organisation in Core."""
    name: str
    """Organisation name as set via Core."""
    feature_analytics: NotRequired[bool]
    """Whether the SDK API should log feature analytics events for this organisation. Defaults to `False`."""
    stop_serving_flags: NotRequired[bool]
    """Whether flag serving is disabled for this organisation. Defaults to `False`."""
    persist_trait_data: NotRequired[bool]
    """If set to `False`, trait data will never be persisted for this organisation. Defaults to `True`."""


class Project(TypedDict):
    """Represents data about a Flagsmith project. Carries settings necessary for an SDK API operation."""

    id: int
    """Unique identifier for the project in Core."""
    name: str
    """Project name as set via Core."""
    organisation: Organisation
    """The organisation that this project belongs to."""
    segments: list[Segment]
    """List of segments."""
    server_key_only_feature_ids: NotRequired[list[int]]
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


class _EnvironmentFields(TypedDict):
    """Common fields for Environment documents."""

    name: NotRequired[str]
    """Environment name. Defaults to an empty string if not set."""
    updated_at: NotRequired[DateTimeStr | None]
    """Last updated timestamp. If not set, current timestamp should be assumed."""

    project: Project
    """Project-specific data for this environment."""
    feature_states: list[FeatureState]
    """List of feature states representing the environment defaults."""

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


### Root document schemas below. Indexed fields are marked as **INDEXED** in the docstrings. ###


class EnvironmentAPIKey(TypedDict):
    """Represents a server-side API key for a Flagsmith environment.

    **DynamoDB table**: `flagsmith_environment_api_key`
    """

    id: int
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
    identity_features: NotRequired[list[FeatureState]]
    """List of identity overrides for this identity."""
    identity_traits: list[Trait]
    """List of traits associated with this identity."""
    django_id: NotRequired[int | None]
    """Unique identifier for the identity in Core. TODO: document why and when this can be `None`."""


class Environment(_EnvironmentFields):
    """Represents a Flagsmith environment. Carries all necessary data for flag evaluation within the environment.

    **DynamoDB table**: `flagsmith_environments`
    """

    id: int
    """Unique identifier for the environment in Core. **INDEXED**."""
    api_key: str
    """Public client-side API key for the environment. **INDEXED**."""


class EnvironmentV2Meta(_EnvironmentFields):
    """Represents a Flagsmith environment. Carries all necessary data for flag evaluation within the environment.

    **DynamoDB table**: `flagsmith_environments_v2`
    """

    environment_id: str
    """Unique identifier for the environment in Core. **INDEXED**."""
    environment_api_key: str
    """Public client-side API key for the environment. **INDEXED**."""
    document_key: Literal["_META"]
    """The fixed document key for the environment v2 document. Always `"_META"`. **INDEXED**."""

    id: int
    """Unique identifier for the environment in Core. Exists for compatibility with the API environment document schema."""


class EnvironmentV2IdentityOverride(TypedDict):
    """Represents an identity override.

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
    """The UUID for this identity. **INDEXED**."""
    feature_state: FeatureState
    """The feature state override for this identity."""
