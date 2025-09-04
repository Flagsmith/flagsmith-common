import json

import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from django.db.utils import OperationalError
from pyfakefs.fake_filesystem import FakeFilesystem
from pytest_django.fixtures import DjangoAssertNumQueries, SettingsWrapper
from pytest_mock import MockerFixture, MockType

from common.core.utils import (
    _replica_sequential_names_by_prefix,
    get_file_contents,
    get_version,
    get_version_info,
    get_versions_from_manifest,
    has_email_provider,
    is_database_replica_setup,
    is_enterprise,
    is_oss,
    is_saas,
    using_database_replica,
)
from tests import GetLogsFixture

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def clear_lru_caches() -> None:
    get_file_contents.cache_clear()
    get_versions_from_manifest.cache_clear()
    has_email_provider.cache_clear()
    is_enterprise.cache_clear()
    is_saas.cache_clear()


@pytest.fixture(autouse=True)
def clear_sequential_replica_manager() -> None:
    """Reset the sequential replica cycle"""
    _replica_sequential_names_by_prefix.clear()


@pytest.fixture()
def bad_replica(mocker: MockerFixture) -> MockType:
    """An unhealthy replica"""
    replica: MockType = mocker.Mock(spec=connections["default"])
    replica.ensure_connection.side_effect = OperationalError("Connection failed")
    return replica


def test__is_oss_for_enterprise_returns_false(fs: FakeFilesystem) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")

    # Then
    assert is_oss() is False


def test__is_oss_for_saas_returns_false(fs: FakeFilesystem) -> None:
    # Given
    fs.create_file("./SAAS_DEPLOYMENT")

    # Then
    assert is_oss() is False


def test__is_oss_for_oss_returns_true(fs: FakeFilesystem) -> None:
    # Then
    assert is_oss() is True


def test_get_version_info(fs: FakeFilesystem) -> None:
    # Given
    expected_manifest_contents = {
        ".": "2.66.2",
    }

    fs.create_file("./ENTERPRISE_VERSION")
    fs.create_file(".versions.json", contents=json.dumps(expected_manifest_contents))
    fs.create_file("./CI_COMMIT_SHA", contents="some_sha")

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "some_sha",
        "image_tag": "2.66.2",
        "has_email_provider": False,
        "is_enterprise": True,
        "is_saas": False,
        "package_versions": {".": "2.66.2"},
        "self_hosted_data": {
            "has_logins": False,
            "has_users": False,
        },
    }


def test_get_version_info_with_missing_files(fs: FakeFilesystem) -> None:
    # Given
    fs.create_file("./ENTERPRISE_VERSION")

    # When
    result = get_version_info()

    # Then
    assert result == {
        "ci_commit_sha": "unknown",
        "image_tag": "unknown",
        "has_email_provider": False,
        "is_enterprise": True,
        "is_saas": False,
        "package_versions": {".": "unknown"},
        "self_hosted_data": {
            "has_logins": False,
            "has_users": False,
        },
    }


EMAIL_BACKENDS_AND_SETTINGS = [
    ("django.core.mail.backends.smtp.EmailBackend", "EMAIL_HOST_USER"),
    ("django_ses.SESBackend", "AWS_SES_REGION_ENDPOINT"),
    ("sgbackend.SendGridBackend", "SENDGRID_API_KEY"),
]


@pytest.mark.parametrize(
    "email_backend,expected_setting_name",
    EMAIL_BACKENDS_AND_SETTINGS,
)
def test_get_version_info__email_config_enabled__return_expected(
    settings: SettingsWrapper,
    email_backend: str,
    expected_setting_name: str,
) -> None:
    # Given
    settings.EMAIL_BACKEND = email_backend
    setattr(settings, expected_setting_name, "value")

    # When
    result = get_version_info()

    # Then
    assert result["has_email_provider"] is True


@pytest.mark.parametrize(
    "email_backend,expected_setting_name",
    [
        (None, None),
        *EMAIL_BACKENDS_AND_SETTINGS,
    ],
)
def test_get_version_info__email_config_disabled__return_expected(
    settings: SettingsWrapper,
    email_backend: str | None,
    expected_setting_name: str | None,
) -> None:
    # Given
    settings.EMAIL_BACKEND = email_backend
    if expected_setting_name:
        setattr(settings, expected_setting_name, None)

    # When
    result = get_version_info()

    # Then
    assert result["has_email_provider"] is False


def test_get_version__valid_file_contents__returns_version_number(
    fs: FakeFilesystem,
) -> None:
    # Given
    fs.create_file("./.versions.json", contents='{".": "v1.2.3"}')

    # When
    result = get_version()

    # Then
    assert result == "v1.2.3"


@pytest.mark.parametrize(
    "manifest_contents",
    [
        '{"foo": "bar"}',
        "",
    ],
)
def test_get_version__invalid_file_contents__returns_unknown(
    fs: FakeFilesystem,
    manifest_contents: str,
) -> None:
    # Given
    fs.create_file("./.versions.json", contents=manifest_contents)

    # When
    result = get_version()

    # Then
    assert result == "unknown"


@pytest.mark.parametrize(
    ["database_names", "expected"],
    [
        ({"default"}, False),
        ({"default", "another_database_with_'replica'_in_its_name"}, False),
        ({"default", "task_processor"}, False),
        ({"default", "replica_1"}, True),
        ({"default", "replica_1", "replica_2"}, True),
        ({"default", "cross_region_replica_1"}, True),
        ({"default", "replica_1", "cross_region_replica_1"}, True),
    ],
)
def test_is_database_replica_setup__tells_whether_any_replica_is_present(
    database_names: list[str],
    expected: bool,
    mocker: MockerFixture,
) -> None:
    # Given
    is_database_replica_setup.cache_clear()
    mocker.patch(
        "common.core.utils.connections",
        {name: connections["default"] for name in database_names},
    )

    # When
    result = is_database_replica_setup()

    # Then
    assert result is expected


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__no_replicas__points_to_default(
    django_assert_num_queries: DjangoAssertNumQueries,
    get_logs: GetLogsFixture,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch("common.core.utils.connections", {"default": connections["default"]})
    manager = get_user_model().objects

    # When / Then
    with django_assert_num_queries(1, using="default"):
        using_database_replica(manager).first()

    assert get_logs("common.core.utils") == [
        ("INFO", "No replicas set up."),
    ]


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__distributed__picks_databases_randomly(
    django_assert_max_num_queries: DjangoAssertNumQueries,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = "distributed"
    manager = get_user_model().objects

    # When / Then
    with django_assert_max_num_queries(20, using="replica_1") as captured:
        for _ in range(20):
            using_database_replica(manager).first()
    assert captured.final_queries
    with django_assert_max_num_queries(20, using="replica_2") as captured:
        for _ in range(20):
            using_database_replica(manager).first()
    assert captured.final_queries
    with django_assert_max_num_queries(20, using="replica_3") as captured:
        for _ in range(20):
            using_database_replica(manager).first()
    assert captured.final_queries


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__distributed__skips_unhealthy_replica(
    bad_replica: MockType,
    django_assert_num_queries: DjangoAssertNumQueries,
    get_logs: GetLogsFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = "distributed"
    manager = get_user_model().objects
    mocker.patch(
        "common.core.utils.connections",
        {
            "default": connections["default"],
            "replica_1": bad_replica,
            "replica_2": connections["replica_2"],
            "replica_3": connections["replica_3"],
            "cross_region_replica_1": connections["cross_region_replica_1"],
            "cross_region_replica_2": connections["cross_region_replica_2"],
        },
    )

    # When / Then
    with django_assert_num_queries(0, using="replica_1"):
        for _ in range(20):
            using_database_replica(manager).first()

    assert set(get_logs("common.core.utils")) == {
        ("ERROR", "Replica 'replica_1' is not available."),
    }


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__distributed__falls_back_to_cross_region_replica(
    bad_replica: MockType,
    django_assert_max_num_queries: DjangoAssertNumQueries,
    get_logs: GetLogsFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = "distributed"
    manager = get_user_model().objects
    bad_replica = mocker.Mock()
    bad_replica.ensure_connection.side_effect = OperationalError("Connection failed")
    mocker.patch(
        "common.core.utils.connections",
        {
            "default": connections["default"],
            "replica_1": bad_replica,
            "replica_2": bad_replica,
            "replica_3": bad_replica,
            "cross_region_replica_1": connections["cross_region_replica_1"],
            "cross_region_replica_2": connections["cross_region_replica_2"],
        },
    )

    # When / Then
    with django_assert_max_num_queries(20, using="cross_region_replica_1") as captured:
        for _ in range(20):
            using_database_replica(manager).first()
    assert captured.final_queries
    with django_assert_max_num_queries(20, using="cross_region_replica_2") as captured:
        for _ in range(20):
            using_database_replica(manager).first()
    assert captured.final_queries

    logs = get_logs("common.core.utils")
    assert (
        {
            ("ERROR", "Replica 'replica_1' is not available."),
            ("ERROR", "Replica 'replica_2' is not available."),
            ("ERROR", "Replica 'replica_3' is not available."),
        }
        == set(logs[0:3])
        == set(logs[4:7])
        # ..And so on
    )
    assert (
        ("WARNING", "Falling back to cross-region replicas, if any.")
        == logs[3]
        == logs[7]
        # ...And so on
    )


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__sequential__picks_databases_sequentially(
    django_assert_num_queries: DjangoAssertNumQueries,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = "sequential"
    manager = get_user_model().objects

    # When / Then
    with django_assert_num_queries(1, using="replica_1"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="replica_2"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="replica_3"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="replica_1"):
        using_database_replica(manager).first()


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__sequential__skips_unhealthy_replica(
    bad_replica: MockType,
    django_assert_num_queries: DjangoAssertNumQueries,
    get_logs: GetLogsFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = "sequential"
    manager = get_user_model().objects
    mocker.patch(
        "common.core.utils.connections",
        {
            "default": connections["default"],
            "replica_1": connections["replica_1"],
            "replica_2": bad_replica,
            "replica_3": connections["replica_3"],
            "cross_region_replica_1": connections["cross_region_replica_1"],
            "cross_region_replica_2": connections["cross_region_replica_2"],
        },
    )

    # When / Then
    with django_assert_num_queries(1, using="replica_1"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="replica_3"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="replica_1"):
        using_database_replica(manager).first()

    assert get_logs("common.core.utils") == [
        ("ERROR", "Replica 'replica_2' is not available."),
    ]


@pytest.mark.django_db(databases="__all__")
def test_using_database_replica__sequential__falls_back_to_cross_region_replica(
    bad_replica: MockType,
    django_assert_num_queries: DjangoAssertNumQueries,
    get_logs: GetLogsFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = "sequential"
    manager = get_user_model().objects
    bad_replica = mocker.Mock()
    bad_replica.ensure_connection.side_effect = OperationalError("Connection failed")
    mocker.patch(
        "common.core.utils.connections",
        {
            "default": connections["default"],
            "replica_1": bad_replica,
            "replica_2": bad_replica,
            "replica_3": bad_replica,
            "cross_region_replica_1": connections["cross_region_replica_1"],
            "cross_region_replica_2": connections["cross_region_replica_2"],
        },
    )

    # When / Then
    with django_assert_num_queries(1, using="cross_region_replica_1"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="cross_region_replica_2"):
        using_database_replica(manager).first()
    with django_assert_num_queries(1, using="cross_region_replica_1"):
        using_database_replica(manager).first()

    assert get_logs("common.core.utils") == 3 * [
        ("ERROR", "Replica 'replica_1' is not available."),
        ("ERROR", "Replica 'replica_2' is not available."),
        ("ERROR", "Replica 'replica_3' is not available."),
        ("WARNING", "Falling back to cross-region replicas, if any."),
    ]


@pytest.mark.django_db(databases="__all__")
@pytest.mark.parametrize("strategy", ["distributed", "sequential"])
def test_using_database_replica__all_replicas_unavailable__falls_back_to_default_database(
    django_assert_num_queries: DjangoAssertNumQueries,
    bad_replica: MockType,
    get_logs: GetLogsFixture,
    mocker: MockerFixture,
    settings: SettingsWrapper,
    strategy: str,
) -> None:
    # Given
    settings.REPLICA_READ_STRATEGY = strategy
    manager = get_user_model().objects
    bad_replica = mocker.Mock()
    bad_replica.ensure_connection.side_effect = OperationalError("Connection failed")
    mocker.patch(
        "common.core.utils.connections",
        {
            "default": connections["default"],
            "replica_1": bad_replica,
            "replica_2": bad_replica,
            "replica_3": bad_replica,
            "cross_region_replica_1": bad_replica,
            "cross_region_replica_2": bad_replica,
        },
    )

    # When / Then
    with django_assert_num_queries(1, using="default"):
        using_database_replica(manager).first()

    logs = get_logs("common.core.utils")
    log_iterator = {"distributed": set, "sequential": list}[strategy]
    assert log_iterator(logs[0:3]) == log_iterator(
        [
            ("ERROR", "Replica 'replica_1' is not available."),
            ("ERROR", "Replica 'replica_2' is not available."),
            ("ERROR", "Replica 'replica_3' is not available."),
        ]
    )
    assert logs[3] == ("WARNING", "Falling back to cross-region replicas, if any.")
    assert log_iterator(logs[4:6]) == log_iterator(
        [
            ("ERROR", "Replica 'cross_region_replica_1' is not available."),
            ("ERROR", "Replica 'cross_region_replica_2' is not available."),
        ]
    )
    assert logs[6] == ("WARNING", "No replicas available.")
