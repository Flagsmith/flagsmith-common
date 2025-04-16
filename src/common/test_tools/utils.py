from typing import Literal

from common.core.utils import is_enterprise, is_saas


def edition_printer() -> Literal["saas!", "enterprise!", "oss!"]:
    if is_saas():
        return "saas!"
    if is_enterprise():
        return "enterprise!"
    return "oss!"
