from typing import Any

_utils = ("Histogram",)


def __getattr__(name: str) -> Any:
    """
    Since utils imports django.conf.settings, we lazy load any objects that
    we want to import to prevent django.core.exceptions.ImproperlyConfigured
    due to settings not being configured.
    """
    if name in _utils:
        from common.prometheus import utils

        return getattr(utils, name)
    raise AttributeError(name)
