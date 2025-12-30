from importlib.util import find_spec

PYDANTIC_INSTALLED = find_spec("pydantic") is not None
