from pytest_mock import MockerFixture

from common.core import middleware as middleware_module


def test_APIResponseVersionHeaderMiddleware__adds_version_header(
    mocker: MockerFixture,
) -> None:
    # Given
    request = mocker.Mock()
    response = mocker.Mock(headers={})
    get_response = mocker.Mock(return_value=response)
    middleware = middleware_module.APIResponseVersionHeaderMiddleware(get_response)
    get_version_number = mocker.patch.object(
        middleware_module,
        "get_version_number",
        return_value="v1.2.3",
    )

    # When
    result = middleware(request)

    # Then
    assert result == response
    assert response.headers["Flagsmith-Version"] == "v1.2.3"
    get_response.assert_called_once_with(request)
    get_version_number.assert_called_once_with()
