from typing import Callable

GetLogsFixture = Callable[[str], list[tuple[str, str]]]
