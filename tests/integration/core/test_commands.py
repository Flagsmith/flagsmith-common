import subprocess
from pathlib import Path

import prometheus_client
import pytest
from django.core.management import call_command
from pytest_mock import MockerFixture

from common.test_tools import SnapshotFixture


@pytest.mark.django_db
def test_docgen__metrics__runs_expected(
    test_metric: prometheus_client.Counter,
    capsys: pytest.CaptureFixture[str],
    snapshot: SnapshotFixture,
) -> None:
    # Given
    argv = ["docgen", "metrics"]
    expected_stdout = snapshot()

    # When
    call_command(*argv)

    # Then
    assert capsys.readouterr().out == expected_stdout


@pytest.fixture
def fixture_app(tmp_path: Path) -> Path:
    """Write a two-file fixture app under `tmp_path/api/fixture_app`."""
    app_path = tmp_path / "api" / "fixture_app"
    app_path.mkdir(parents=True)
    (app_path / "views.py").write_text(
        """\
import structlog

logger = structlog.get_logger("code_references")


def perform_create() -> None:
    logger.info(
        "scan.created",
        organisation__id=1,
        code_references__count=2,
    )
"""
    )
    (app_path / "nested").mkdir()
    (app_path / "nested/workflows.py").write_text(
        """\
import structlog

logger = structlog.get_logger("workflows")


def publish() -> None:
    logger.bind(workflow_id=1).info("published", status="ok")
"""
    )
    return app_path


@pytest.fixture
def patched_apps(fixture_app: Path, mocker: MockerFixture) -> None:
    """Patch `docgen.apps` so only the fixture app is scanned."""
    fake_config = mocker.Mock()
    fake_config.path = str(fixture_app)
    fake_config.label = "fixture_app"
    fake_config.name = "fixture_app"
    mock_apps = mocker.patch("common.core.management.commands.docgen.apps")
    mock_apps.get_app_configs.return_value = [fake_config]


@pytest.mark.django_db
def test_docgen__events__runs_expected(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    patched_apps: None,
    snapshot: SnapshotFixture,
) -> None:
    # Given — `tmp_path` is a real git repo, so `_get_repo_root` resolves
    # paths against it without mocking the subprocess call.
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    monkeypatch.chdir(tmp_path)
    expected_stdout = snapshot()

    # When
    call_command("docgen", "events")

    # Then
    assert capsys.readouterr().out == expected_stdout


@pytest.mark.django_db
def test_docgen__events_not_in_git_repo__falls_back_to_cwd(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    patched_apps: None,
) -> None:
    # Given — no `git init`; `_get_repo_root` swallows the
    # `CalledProcessError` and falls back to `Path.cwd()`, which we pin to
    # `tmp_path` via `monkeypatch.chdir`.
    monkeypatch.chdir(tmp_path)

    # When
    call_command("docgen", "events")

    # Then
    stdout = capsys.readouterr().out
    assert " - `api/fixture_app/views.py:7`" in stdout
    assert " - `api/fixture_app/nested/workflows.py:7`" in stdout


@pytest.mark.django_db
def test_docgen__events_app_outside_repo_root__keeps_absolute_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    fixture_app: Path,
    patched_apps: None,
) -> None:
    # Given — the resolved repo root and the fixture app live in *different*
    # subtrees under `tmp_path`, so `_relative_if_under` hits its `ValueError`
    # branch and keeps the absolute path on each emitted location.
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    monkeypatch.chdir(repo_root)

    # When
    call_command("docgen", "events")

    # Then
    stdout = capsys.readouterr().out
    assert f" - `{fixture_app}/views.py:7`" in stdout
    assert f" - `{fixture_app}/nested/workflows.py:7`" in stdout
