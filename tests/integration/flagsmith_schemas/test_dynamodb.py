from decimal import Decimal
from typing import TypeVar

import pytest
from pydantic import TypeAdapter, ValidationError
from pytest_mock import MockerFixture

from flagsmith_schemas.dynamodb import (
    Environment,
    EnvironmentAPIKey,
    EnvironmentV2IdentityOverride,
    EnvironmentV2Meta,
    Identity,
)
from flagsmith_schemas.types import DateTimeStr, UUIDStr

T = TypeVar("T")


@pytest.mark.parametrize(
    ("document_type", "json_data_filename", "expected_result"),
    [
        pytest.param(
            Environment,
            "flagsmith_environments.json",
            {
                "id": Decimal("12561"),
                "api_key": "n9fbf9h3v4fFgH3U3ngWhb",
                "project": {
                    "id": Decimal("5359"),
                    "name": "Edge API Test Project",
                    "organisation": {
                        "id": Decimal("13"),
                        "name": "Flagsmith",
                        "feature_analytics": False,
                        "stop_serving_flags": False,
                        "persist_trait_data": True,
                    },
                    "segments": [
                        {
                            "id": Decimal("4267"),
                            "name": "regular_segment",
                            "rules": [
                                {
                                    "type": "ALL",
                                    "rules": [
                                        {
                                            "type": "ANY",
                                            "rules": [],
                                            "conditions": [
                                                {
                                                    "operator": "LESS_THAN",
                                                    "value": "40",
                                                    "property_": "age",
                                                }
                                            ],
                                        },
                                        {
                                            "type": "ANY",
                                            "rules": [],
                                            "conditions": [
                                                {
                                                    "operator": "GREATER_THAN_INCLUSIVE",
                                                    "value": "21",
                                                    "property_": "age",
                                                }
                                            ],
                                        },
                                        {
                                            "type": "ANY",
                                            "rules": [],
                                            "conditions": [
                                                {
                                                    "operator": "EQUAL",
                                                    "value": "green",
                                                    "property_": "favourite_colour",
                                                },
                                                {
                                                    "operator": "EQUAL",
                                                    "value": "blue",
                                                    "property_": "favourite_colour",
                                                },
                                            ],
                                        },
                                    ],
                                    "conditions": [],
                                }
                            ],
                            "feature_states": [
                                {
                                    "feature": {
                                        "id": Decimal("15058"),
                                        "name": "string_feature",
                                        "type": "STANDARD",
                                    },
                                    "enabled": False,
                                    "feature_state_value": "segment_override",
                                    "django_id": Decimal("81027"),
                                    "multivariate_feature_state_values": [],
                                }
                            ],
                        },
                        {
                            "id": Decimal("4268"),
                            "name": "10_percent",
                            "rules": [
                                {
                                    "type": "ALL",
                                    "rules": [
                                        {
                                            "type": "ANY",
                                            "rules": [],
                                            "conditions": [
                                                {
                                                    "operator": "PERCENTAGE_SPLIT",
                                                    "value": "0.1",
                                                    "property_": "",
                                                }
                                            ],
                                        }
                                    ],
                                    "conditions": [],
                                }
                            ],
                            "feature_states": [
                                {
                                    "feature": {
                                        "id": Decimal("15060"),
                                        "name": "basic_flag",
                                        "type": "STANDARD",
                                    },
                                    "enabled": True,
                                    "feature_state_value": "",
                                    "django_id": Decimal("81026"),
                                    "multivariate_feature_state_values": [],
                                }
                            ],
                        },
                        {
                            "id": Decimal("16"),
                            "name": "segment_two",
                            "rules": [
                                {
                                    "type": "ALL",
                                    "rules": [
                                        {
                                            "type": "ANY",
                                            "rules": [],
                                            "conditions": [
                                                {
                                                    "operator": "EQUAL",
                                                    "value": "2",
                                                    "property_": "two",
                                                },
                                                {
                                                    "operator": "IS_SET",
                                                    "value": None,
                                                    "property_": "two",
                                                },
                                            ],
                                        }
                                    ],
                                    "conditions": [],
                                }
                            ],
                            "feature_states": [
                                {
                                    "feature": {
                                        "id": Decimal("15058"),
                                        "name": "string_feature",
                                        "type": "STANDARD",
                                    },
                                    "enabled": True,
                                    "feature_state_value": "segment_two_override_priority_0",
                                    "django_id": Decimal("78978"),
                                    "featurestate_uuid": UUIDStr(
                                        "1545809c-e97f-4a1f-9e67-8b4f2b396aa6"
                                    ),
                                    "feature_segment": {"priority": Decimal("0")},
                                    "multivariate_feature_state_values": [],
                                }
                            ],
                        },
                        {
                            "id": Decimal("17"),
                            "name": "segment_three",
                            "rules": [
                                {
                                    "type": "ALL",
                                    "rules": [
                                        {
                                            "type": "ALL",
                                            "rules": [],
                                            "conditions": [
                                                {
                                                    "operator": "EQUAL",
                                                    "value": "3",
                                                    "property_": "three",
                                                },
                                                {
                                                    "operator": "IS_NOT_SET",
                                                    "value": None,
                                                    "property_": "something_that_is_not_set",
                                                },
                                            ],
                                        }
                                    ],
                                    "conditions": [],
                                }
                            ],
                            "feature_states": [
                                {
                                    "feature": {
                                        "id": Decimal("15058"),
                                        "name": "string_feature",
                                        "type": "STANDARD",
                                    },
                                    "enabled": True,
                                    "feature_state_value": "segment_three_override_priority_1",
                                    "django_id": Decimal("78977"),
                                    "featurestate_uuid": UUIDStr(
                                        "1545809c-e97f-4a1f-9e67-8b4f2b396aa7"
                                    ),
                                    "feature_segment": {"priority": Decimal("1")},
                                    "multivariate_feature_state_values": [],
                                }
                            ],
                        },
                    ],
                    "hide_disabled_flags": False,
                },
                "feature_states": [
                    {
                        "feature": {
                            "id": Decimal("15058"),
                            "name": "string_feature",
                            "type": "STANDARD",
                        },
                        "enabled": True,
                        "feature_state_value": "foo",
                        "django_id": Decimal("78978"),
                        "feature_segment": None,
                        "multivariate_feature_state_values": [],
                    },
                    {
                        "feature": {
                            "id": Decimal("15059"),
                            "name": "integer_feature",
                            "type": "STANDARD",
                        },
                        "enabled": True,
                        "feature_state_value": Decimal("1234"),
                        "django_id": Decimal("78980"),
                        "multivariate_feature_state_values": [],
                    },
                    {
                        "feature": {
                            "id": Decimal("15060"),
                            "name": "basic_flag",
                            "type": "STANDARD",
                        },
                        "enabled": False,
                        "feature_state_value": None,
                        "django_id": Decimal("78982"),
                        "multivariate_feature_state_values": [],
                    },
                    {
                        "feature": {
                            "id": Decimal("15061"),
                            "name": "float_feature",
                            "type": "STANDARD",
                        },
                        "enabled": True,
                        "feature_state_value": "12.34",
                        "django_id": Decimal("78984"),
                        "multivariate_feature_state_values": [],
                    },
                    {
                        "feature": {
                            "id": Decimal("15062"),
                            "name": "mv_feature",
                            "type": "MULTIVARIATE",
                        },
                        "enabled": True,
                        "feature_state_value": "foo",
                        "django_id": Decimal("78986"),
                        "multivariate_feature_state_values": [
                            {
                                "id": Decimal("3404"),
                                "percentage_allocation": Decimal("30"),
                                "multivariate_feature_option": {"value": "baz"},
                            },
                            {
                                "id": Decimal("3402"),
                                "percentage_allocation": Decimal("30"),
                                "multivariate_feature_option": {"value": "bar"},
                            },
                            {
                                "id": Decimal("3405"),
                                "percentage_allocation": Decimal("0"),
                                "multivariate_feature_option": {"value": Decimal("1")},
                            },
                            {
                                "id": Decimal("3406"),
                                "percentage_allocation": Decimal("0"),
                                "multivariate_feature_option": {"value": True},
                            },
                        ],
                    },
                ],
            },
            id="flagsmith_environments",
        ),
        pytest.param(
            EnvironmentAPIKey,
            "flagsmith_environment_api_key.json",
            {
                "key": "ser.ZSwVCQrCGpXXKdvVsVxoie",
                "active": True,
                "client_api_key": "pQuzvsMLQoOVAwITrTWDQJ",
                "created_at": DateTimeStr("2023-04-21T13:11:13.913178+00:00"),
                "expires_at": None,
                "id": Decimal("907"),
                "name": "TestKey",
            },
            id="flagsmith_environment_api_key",
        ),
        pytest.param(
            Identity,
            "flagsmith_identities.json",
            {
                "composite_key": "pQuzvsMLQoOVAwITrTWDQJ_57c6edf1bbf145a1a23ea287ce44877f",
                "created_date": DateTimeStr("2024-03-19T09:41:22.974595+00:00"),
                "django_id": None,
                "environment_api_key": "pQuzvsMLQoOVAwITrTWDQJ",
                "identifier": "57c6edf1bbf145a1a23ea287ce44877f",
                "identity_features": [
                    {
                        "django_id": None,
                        "enabled": True,
                        "feature": {
                            "id": Decimal("67"),
                            "name": "test_feature",
                            "type": "STANDARD",
                        },
                        "featurestate_uuid": UUIDStr(
                            "20988957-d345-424e-9abc-1dc5a814da48"
                        ),
                        "feature_segment": None,
                        "feature_state_value": None,
                        "multivariate_feature_state_values": [],
                    }
                ],
                "identity_traits": [{"trait_key": "test_trait", "trait_value": 42}],
                "identity_uuid": UUIDStr("118ecfc9-5234-4218-8af8-dd994dbfedc0"),
            },
            id="flagsmith_identities",
        ),
        pytest.param(
            EnvironmentV2Meta,
            "flagsmith_environments_v2:_META.json",
            {
                "environment_id": "49268",
                "document_key": "_META",
                "allow_client_traits": True,
                "amplitude_config": None,
                "dynatrace_config": None,
                "environment_api_key": "AQ9T6LixPqYMJkuqGJy3t2",
                "feature_states": [
                    {
                        "django_id": Decimal("577621"),
                        "enabled": True,
                        "feature": {
                            "id": Decimal("100298"),
                            "name": "test_feature",
                            "type": "MULTIVARIATE",
                        },
                        "featurestate_uuid": UUIDStr(
                            "42d7805e-a9ac-401c-a7b7-d6583ac5a365"
                        ),
                        "feature_segment": None,
                        "feature_state_value": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
                        "multivariate_feature_state_values": [
                            {
                                "id": Decimal("185130"),
                                "multivariate_feature_option": {
                                    "id": Decimal("20919"),
                                    "value": "second",
                                },
                                "mv_fs_value_uuid": UUIDStr(
                                    "0b02ce41-9965-4c61-8b96-c8d76e3d4a27"
                                ),
                                "percentage_allocation": Decimal("10.0"),
                            },
                            {
                                "id": Decimal("48717"),
                                "multivariate_feature_option": {
                                    "id": Decimal("14004"),
                                    "value": True,
                                },
                                "mv_fs_value_uuid": UUIDStr(
                                    "cb05f49c-de1f-44f1-87eb-c3b55d473063"
                                ),
                                "percentage_allocation": Decimal("30.0"),
                            },
                        ],
                    },
                    {
                        "django_id": Decimal("1041292"),
                        "enabled": False,
                        "feature": {
                            "id": Decimal("172422"),
                            "name": "feature",
                            "type": "STANDARD",
                        },
                        "featurestate_uuid": UUIDStr(
                            "58b7b954-1b75-493a-82df-5be0efeedd2a"
                        ),
                        "feature_segment": None,
                        "feature_state_value": Decimal("3"),
                        "multivariate_feature_state_values": [],
                    },
                ],
                "heap_config": None,
                "hide_disabled_flags": None,
                "hide_sensitive_data": False,
                "id": Decimal("49268"),
                "mixpanel_config": None,
                "name": "Development",
                "project": {
                    "enable_realtime_updates": False,
                    "hide_disabled_flags": False,
                    "id": Decimal("19368"),
                    "name": "Example Project",
                    "organisation": {
                        "feature_analytics": False,
                        "id": Decimal("13"),
                        "name": "Flagsmith",
                        "persist_trait_data": True,
                        "stop_serving_flags": False,
                    },
                    "segments": [
                        {
                            "feature_states": [],
                            "id": Decimal("44126"),
                            "name": "test",
                            "rules": [
                                {
                                    "conditions": [],
                                    "rules": [
                                        {
                                            "conditions": [
                                                {
                                                    "operator": "EQUAL",
                                                    "property_": "test",
                                                    "value": "test",
                                                }
                                            ],
                                            "rules": [],
                                            "type": "ANY",
                                        }
                                    ],
                                    "type": "ALL",
                                }
                            ],
                        }
                    ],
                    "server_key_only_feature_ids": [],
                },
                "rudderstack_config": None,
                "segment_config": None,
                "updated_at": DateTimeStr("2025-11-16T13:28:31.244331+00:00"),
                "use_identity_composite_key_for_hashing": True,
                "use_identity_overrides_in_local_eval": False,
                "webhook_config": None,
            },
            id="flagsmith_environments_v2:_META",
        ),
        pytest.param(
            EnvironmentV2IdentityOverride,
            "flagsmith_environments_v2:identity_override.json",
            {
                "environment_id": "65061",
                "document_key": "identity_override:136660:3018f59c-77a1-43df-a9a8-38723e99e441",
                "environment_api_key": "pQuzvsMLQoOVAwITrTWDQJ",
                "feature_state": {
                    "django_id": None,
                    "enabled": True,
                    "feature": {
                        "id": Decimal("136660"),
                        "name": "test1",
                        "type": "STANDARD",
                    },
                    "featurestate_uuid": UUIDStr(
                        "652d8931-37d9-438e-9825-f525b9e83077"
                    ),
                    "feature_segment": None,
                    "feature_state_value": "test_override_value",
                    "multivariate_feature_state_values": [],
                },
                "identifier": "Development_user_123456",
                "identity_uuid": UUIDStr("3018f59c-77a1-43df-a9a8-38723e99e441"),
            },
        ),
    ],
)
def test_document__validate_json__expected_result(
    request: pytest.FixtureRequest,
    document_type: type[T],
    json_data_filename: str,
    expected_result: T,
) -> None:
    # Given
    type_adapter = TypeAdapter(document_type)
    json_data = request.path.parent.joinpath(f"data/{json_data_filename}").read_text()

    # When
    document = type_adapter.validate_json(json_data)

    # Then
    assert document == expected_result


def test_type_adapter__identity__duplicate_features__raises_expected(
    mocker: MockerFixture,
) -> None:
    # Given
    type_adapter = TypeAdapter(Identity)
    python_data = {
        "composite_key": "envkey_identifier",
        "created_date": "2024-03-19T09:41:22.974595+00:00",
        "environment_api_key": "envkey",
        "identifier": "identifier",
        "identity_uuid": "118ecfc9-5234-4218-8af8-dd994dbfedc0",
        "identity_features": [
            {
                "enabled": True,
                "feature": {"id": 1, "name": "feature1", "type": "STANDARD"},
                "feature_state_value": None,
                "multivariate_feature_state_values": [],
            },
            {
                "enabled": False,
                "feature": {"id": 1, "name": "feature1", "type": "STANDARD"},
                "feature_state_value": "override",
                "multivariate_feature_state_values": [],
            },
        ],
        "identity_traits": [],
    }

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        type_adapter.validate_python(python_data)

    assert len(exc_info.value.errors()) == 1
    assert (
        exc_info.value.errors()[0].items()
        >= {
            "type": "value_error",
            "loc": ("identity_features",),
            "msg": "Value error, Feature id=1 cannot have multiple feature states for a single identity.",
        }.items()
    )


def test_type_adapter__environment__multivariate_feature_states_percentage_allocation_exceeds_100__raises_expected() -> (
    None
):
    # Given
    type_adapter = TypeAdapter(Environment)
    python_data = {
        "id": 1,
        "api_key": "envkey",
        "project": {
            "id": 1,
            "name": "Project",
            "organisation": {
                "id": 1,
                "name": "Org",
                "feature_analytics": False,
                "stop_serving_flags": False,
                "persist_trait_data": True,
            },
            "segments": [],
            "hide_disabled_flags": False,
        },
        "feature_states": [
            {
                "feature": {"id": 1, "name": "mv_feature", "type": "MULTIVARIATE"},
                "enabled": True,
                "feature_state_value": "some_value",
                "django_id": 1,
                "multivariate_feature_state_values": [
                    {
                        "id": 1,
                        "percentage_allocation": 60.0,
                        "multivariate_feature_option": {"value": "option1"},
                    },
                    {
                        "id": 2,
                        "percentage_allocation": 50.0,
                        "multivariate_feature_option": {"value": "option2"},
                    },
                ],
            }
        ],
    }

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        type_adapter.validate_python(python_data)

    assert len(exc_info.value.errors()) == 1
    assert (
        exc_info.value.errors()[0].items()
        >= {
            "type": "value_error",
            "loc": ("feature_states", 0, "multivariate_feature_state_values"),
            "msg": "Value error, Total `percentage_allocation` of multivariate feature state values cannot exceed 100.",
        }.items()
    )
