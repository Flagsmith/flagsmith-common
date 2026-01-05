from importlib.util import find_spec

PYDANTIC_INSTALLED = find_spec("pydantic") is not None
MAX_STRING_FEATURE_STATE_VALUE_LENGTH = 20_000
