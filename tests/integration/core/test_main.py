import io
import subprocess

import django
import pytest
from django.core.management import ManagementUtility

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


def test_main__healthcheck__no_server__runs_expected(
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    argv = ["flagsmith", "healthcheck"]

    # When
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    # Then
    assert "Connection refused args.port=8000" in capsys.readouterr().out
    assert exc_info.value.code == 1


def test_main__healtcheck__server__runs_expected(
    unused_tcp_port: int,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    process = subprocess.Popen(
        ["flagsmith", "start", "-b", f"0.0.0.0:{unused_tcp_port}", "api"],
        stderr=subprocess.PIPE,
    )
    assert process.stderr
    for line in io.TextIOWrapper(process.stderr, "utf-8"):
        if "Listening" in line:
            break

    argv = ["flagsmith", "healthcheck", "--port", str(unused_tcp_port)]

    # When
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    # Then
    assert capsys.readouterr().out[:-1] == "OK"
    assert exc_info.value.code == 0
