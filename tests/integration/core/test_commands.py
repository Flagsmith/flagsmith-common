import prometheus_client
import pytest
from django.core.management import call_command

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
