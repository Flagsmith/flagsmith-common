import django
import pytest
from django.core.management import ManagementUtility
from pytest_httpserver import HTTPServer

from common.core.main import main


@pytest.mark.parametrize(
    "argv, expected_out",
    (
        [["flagsmith"], ManagementUtility(["flagsmith"]).main_help_text()],
        [["flagsmith", "version"], django.get_version()],
    ),
)
def test_main__non_overridden_args__defaults_to_django(
    argv: list[str],
    expected_out: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given & When
    main(argv)

    # Then
    assert capsys.readouterr().out[:-1] == expected_out


def test_main__healthcheck_tcp__no_server__runs_expected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    argv = ["flagsmith", "healthcheck", "tcp"]

    # When
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    # Then
    assert "Connection refused port=8000" in capsys.readouterr().out
    assert exc_info.value.code == 1


def test_main__healtcheck_tcp__server__runs_expected(
    unused_tcp_port: int,
    http_server: HTTPServer,
) -> None:
    # Given
    argv = ["flagsmith", "healthcheck", "tcp", "--port", str(unused_tcp_port)]

    # When
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    # Then
    assert exc_info.value.code == 0


def test_main__healtcheck_http__no_server__runs_expected() -> None:
    # Given
    argv = ["flagsmith", "healthcheck", "http"]

    # When & Then
    with pytest.raises(Exception):
        main(argv)


@pytest.mark.parametrize(
    "argv, expected_path",
    (
        (["flagsmith", "healthcheck", "http"], "/health/liveness"),
        (["flagsmith", "healthcheck", "http", "health/readiness"], "/health/readiness"),
    ),
)
def test_main__healthcheck_http__server__runs_expected(
    unused_tcp_port: int,
    http_server: HTTPServer,
    argv: list[str],
    expected_path: str,
) -> None:
    # Given
    argv.extend(["--port", str(unused_tcp_port)])

    http_server.expect_request(expected_path).respond_with_data(status=200)

    # When & Then
    main(argv)


def test_main__healthcheck_http__server_invalid_response__runs_expected(
    unused_tcp_port: int,
    http_server: HTTPServer,
) -> None:
    # Given
    argv = ["flagsmith", "healthcheck", "http", "--port", str(unused_tcp_port)]

    http_server.expect_request("/health/liveness").respond_with_data(status=500)

    # When & Then
    with pytest.raises(Exception):
        main(argv)
