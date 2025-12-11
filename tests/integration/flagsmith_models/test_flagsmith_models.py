from uuid import UUID

from pydantic.type_adapter import TypeAdapter
from pytest import FixtureRequest

from common.test_tools import SnapshotFixture
from flagsmith_models import Environment


def test_environment__validate_json__expected_result(
    request: FixtureRequest,
    snapshot: SnapshotFixture,
) -> None:
    # Given
    type_adapter = TypeAdapter(Environment)
    json_data = request.path.parent.joinpath("data/environment.json").read_text()

    # When
    environment = type_adapter.validate_json(json_data)

    # Then
    assert environment == {
        "id": 12561,
        "api_key": "n9fbf9h3v4fFgH3U3ngWhb",
        "project": {
            "id": 5359,
            "name": "Edge API Test Project",
            "organisation": {
                "id": 13,
                "name": "Flagsmith",
                "feature_analytics": False,
                "stop_serving_flags": False,
                "persist_trait_data": True,
            },
            "segments": [
                {
                    "id": 4267,
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
                                "id": 15058,
                                "name": "string_feature",
                                "type": "STANDARD",
                            },
                            "enabled": False,
                            "feature_state_value": "segment_override",
                            "django_id": 81027,
                            "multivariate_feature_state_values": [],
                        }
                    ],
                },
                {
                    "id": 4268,
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
                                "id": 15060,
                                "name": "basic_flag",
                                "type": "STANDARD",
                            },
                            "enabled": True,
                            "feature_state_value": "",
                            "django_id": 81026,
                            "multivariate_feature_state_values": [],
                        }
                    ],
                },
                {
                    "id": 16,
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
                                "id": 15058,
                                "name": "string_feature",
                                "type": "STANDARD",
                            },
                            "enabled": True,
                            "feature_state_value": "segment_two_override_priority_0",
                            "django_id": 78978,
                            "featurestate_uuid": UUID(
                                "1545809c-e97f-4a1f-9e67-8b4f2b396aa6"
                            ),
                            "feature_segment": {"priority": 0},
                            "multivariate_feature_state_values": [],
                        }
                    ],
                },
                {
                    "id": 17,
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
                                "id": 15058,
                                "name": "string_feature",
                                "type": "STANDARD",
                            },
                            "enabled": True,
                            "feature_state_value": "segment_three_override_priority_1",
                            "django_id": 78977,
                            "featurestate_uuid": UUID(
                                "1545809c-e97f-4a1f-9e67-8b4f2b396aa7"
                            ),
                            "feature_segment": {"priority": 1},
                            "multivariate_feature_state_values": [],
                        }
                    ],
                },
            ],
            "hide_disabled_flags": False,
        },
        "feature_states": [
            {
                "feature": {"id": 15058, "name": "string_feature", "type": "STANDARD"},
                "enabled": True,
                "feature_state_value": "foo",
                "django_id": 78978,
                "feature_segment": None,
                "multivariate_feature_state_values": [],
            },
            {
                "feature": {"id": 15059, "name": "integer_feature", "type": "STANDARD"},
                "enabled": True,
                "feature_state_value": 1234,
                "django_id": 78980,
                "multivariate_feature_state_values": [],
            },
            {
                "feature": {"id": 15060, "name": "basic_flag", "type": "STANDARD"},
                "enabled": False,
                "feature_state_value": None,
                "django_id": 78982,
                "multivariate_feature_state_values": [],
            },
            {
                "feature": {"id": 15061, "name": "float_feature", "type": "STANDARD"},
                "enabled": True,
                "feature_state_value": "12.34",
                "django_id": 78984,
                "multivariate_feature_state_values": [],
            },
            {
                "feature": {"id": 15062, "name": "mv_feature", "type": "MULTIVARIATE"},
                "enabled": True,
                "feature_state_value": "foo",
                "django_id": 78986,
                "multivariate_feature_state_values": [
                    {
                        "id": 3404,
                        "percentage_allocation": 30.0,
                        "multivariate_feature_option": {"value": "baz"},
                    },
                    {
                        "id": 3402,
                        "percentage_allocation": 30.0,
                        "multivariate_feature_option": {"value": "bar"},
                    },
                    {
                        "id": 3405,
                        "percentage_allocation": 0.0,
                        "multivariate_feature_option": {"value": 1},
                    },
                    {
                        "id": 3406,
                        "percentage_allocation": 0.0,
                        "multivariate_feature_option": {"value": True},
                    },
                ],
            },
        ],
    }
