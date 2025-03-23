from typing import get_args

from common.prometheus.types import UnknownLabelValue

UNKNOWN_LABEL_VALUE: UnknownLabelValue = get_args(UnknownLabelValue)[0]
