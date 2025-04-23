import pytest
from pytest_mock import MockerFixture

from common.core import middleware as middleware_module, utils


@pytest.fixture(autouse=True)
def clear_lru_caches() -> None:
    utils.get_file_contents.cache_clear()
    utils.get_versions_from_manifest.cache_clear()


def test_APIResponseVersionHeaderMiddleware__valid_version_info___adds_version_header(
    mocker: MockerFixture,
) -> None:
    # Given
    request = mocker.Mock()
    response = mocker.Mock(headers={})
    get_response = mocker.Mock(return_value=response)
    middleware = middleware_module.APIResponseVersionHeaderMiddleware(get_response)
    get_versions_from_manifest = mocker.patch.object(
        middleware_module, "get_versions_from_manifest",
        return_value={".": "v1.2.3"},
    )

    # When
    result = middleware(request)

    # Then
    assert result == response
    assert response.headers["Flagsmith-Version"] == "v1.2.3"
    get_response.assert_called_once_with(request)
    get_versions_from_manifest.assert_called_once_with()


@pytest.mark.parametrize("version_info", [
    {"foo": "bar"},
    {},
])
def test_APIResponseVersionHeaderMiddleware__invalid_version_info___adds_unknown_header(
    mocker: MockerFixture,
    version_info: dict[str, str] | None,
) -> None:
    # Given
    request = mocker.Mock()
    response = mocker.Mock(headers={})
    get_response = mocker.Mock(return_value=response)
    middleware = middleware_module.APIResponseVersionHeaderMiddleware(get_response)
    get_versions_from_manifest = mocker.patch.object(
        middleware_module, "get_versions_from_manifest",
        return_value=version_info,
    )

    # When
    result = middleware(request)

    # Then
    assert result == response
    assert response.headers["Flagsmith-Version"] == "unknown"
    get_response.assert_called_once_with(request)
    get_versions_from_manifest.assert_called_once_with()