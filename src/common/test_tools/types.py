from pathlib import Path
from typing import Protocol

import pytest


class AssertMetricFixture(Protocol):
    def __call__(
        self,
        *,
        name: str,
        labels: dict[str, str],
        value: float | int,
    ) -> None: ...


class SnapshotFixture(Protocol):
    def __call__(self, name: str = "") -> "Snapshot": ...


class Snapshot:
    """
    Read contents of `path` and make them available for comparison via the `==` operator.
    If the contents are different, and `Snapshot` initialised in update mode,
    (e.g. by running `pytest` with `--snapshot-update`), write the new contents to `path`.
    """

    def __init__(self, path: Path, for_update: bool) -> None:
        self.path = path
        mode = "r" if not for_update else "w+"
        self.content: str = open(path, encoding="utf-8", mode=mode).read()
        self.for_update = for_update

    def __eq__(self, other: object) -> bool:
        if self.content == other:
            return True
        if self.for_update and isinstance(other, str):
            with open(self.path, "w", encoding="utf-8") as f:
                f.write(other)
            pytest.xfail(reason=f"Snapshot updated: {self.path}")
        return False

    def __str__(self) -> str:
        return self.content

    __repr__ = __str__
