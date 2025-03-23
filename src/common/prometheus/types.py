from typing import Literal, TypeAlias

UnknownLabelValue = Literal["unknown"]
LabelValue: TypeAlias = str | UnknownLabelValue
