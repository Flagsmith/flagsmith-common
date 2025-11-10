from typing import Any

_utils = ("Histogram",)


def __getattr__(name: str) -> Any:
    """
    Since utils imports settings, we lazy load any objects that we want to import to
    prevent Django's settings-at-import-time trap
    """
    if name in _utils:
        from common.prometheus import utils

        return getattr(utils, name)
    raise AttributeError(name)
