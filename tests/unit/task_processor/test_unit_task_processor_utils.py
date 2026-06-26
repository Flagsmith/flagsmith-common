import argparse

import pytest

from task_processor.utils import add_arguments


def _parse_defaults() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_arguments(parser)
    return parser.parse_args([])


def test_add_arguments__no_env__uses_run_docker_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    for name in [
        "TASK_PROCESSOR_NUM_THREADS",
        "TASK_PROCESSOR_SLEEP_INTERVAL_MS",
        "TASK_PROCESSOR_SLEEP_INTERVAL",
        "TASK_PROCESSOR_GRACE_PERIOD_MS",
        "TASK_PROCESSOR_QUEUE_POP_SIZE",
    ]:
        monkeypatch.delenv(name, raising=False)

    # When
    args = _parse_defaults()

    # Then
    assert args.numthreads == 5
    assert args.sleepintervalms == 500
    assert args.graceperiodms == 20000
    assert args.queuepopsize == 10


def test_add_arguments__env_set__uses_env_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("TASK_PROCESSOR_NUM_THREADS", "8")
    monkeypatch.setenv("TASK_PROCESSOR_SLEEP_INTERVAL_MS", "250")
    monkeypatch.setenv("TASK_PROCESSOR_GRACE_PERIOD_MS", "15000")
    monkeypatch.setenv("TASK_PROCESSOR_QUEUE_POP_SIZE", "20")

    # When
    args = _parse_defaults()

    # Then
    assert args.numthreads == 8
    assert args.sleepintervalms == 250
    assert args.graceperiodms == 15000
    assert args.queuepopsize == 20


def test_add_arguments__legacy_sleep_interval__used_as_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.delenv("TASK_PROCESSOR_SLEEP_INTERVAL_MS", raising=False)
    monkeypatch.setenv("TASK_PROCESSOR_SLEEP_INTERVAL", "750")

    # When
    args = _parse_defaults()

    # Then
    assert args.sleepintervalms == 750


def test_add_arguments__sleep_interval_ms__takes_precedence_over_legacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    monkeypatch.setenv("TASK_PROCESSOR_SLEEP_INTERVAL_MS", "300")
    monkeypatch.setenv("TASK_PROCESSOR_SLEEP_INTERVAL", "750")

    # When
    args = _parse_defaults()

    # Then
    assert args.sleepintervalms == 300
