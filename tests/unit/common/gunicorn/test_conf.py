from unittest.mock import Mock

from pytest_mock import MockerFixture

from common.gunicorn.conf import child_exit


def test_child_exit__calls_mark_process_dead_with_worker_pid(
    mocker: MockerFixture,
) -> None:
    # Given
    mark_process_dead_mock = mocker.patch("common.gunicorn.conf.mark_process_dead")
    server = Mock()
    worker = Mock()
    worker.pid = 12345

    # When
    child_exit(server, worker)

    # Then
    mark_process_dead_mock.assert_called_once_with(12345)
