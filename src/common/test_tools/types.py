from typing import Protocol


class AssertMetricFixture(Protocol):
    def __call__(
        self,
        *,
        name: str,
        labels: dict[str, str],
        value: float | int,
    ) -> None: ...


class SnapshotFixture(Protocol):
    def __call__(self, name: str = "") -> str: ...
