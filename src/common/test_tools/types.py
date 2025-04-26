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
    def __init__(self, path: Path, for_update: bool) -> None:
        self.path = path
        self.content = open(path).read()
        self.for_update = for_update

    def __eq__(self, other: object) -> bool:
        eq = self.content == other
        if not eq and isinstance(other, str) and self.for_update:
            with open(self.path, "w") as f:
                f.write(other)
                pytest.xfail(reason=f"Snapshot updated: {self.path}")
        return eq

    def __str__(self) -> str:
        return self.content

    __repr__ = __str__
