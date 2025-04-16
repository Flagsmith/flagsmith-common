from typing import Literal

from common.core.utils import is_enterprise, is_saas

EditionPrinterReturnValue = Literal["saas!", "enterprise!", "oss!"]


def edition_printer() -> EditionPrinterReturnValue:
    if is_saas():
        return "saas!"
    if is_enterprise():
        return "enterprise!"
    return "oss!"
