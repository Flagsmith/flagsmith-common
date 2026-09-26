from datetime import datetime
from decimal import Decimal
from functools import partial
from typing import Any
from uuid import UUID

from pydantic import (
    AfterValidator,
    BeforeValidator,
    ValidateAs,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)

from flagsmith_schemas.validators import (
    validate_dynamo_feature_state_value,
    validate_identity_feature_states,
    validate_multivariate_feature_state_values,
)


def _keep_stored_decimal(
    value: Any, handler: ValidatorFunctionWrapHandler, *, integral: bool
) -> Decimal:
    # DynamoDB reads numbers back as `Decimal`s: keep them as they are.
    if isinstance(value, Decimal) and (
        not integral or value == value.to_integral_value()
    ):
        return value
    validated: Decimal = handler(value)
    return validated


ValidateDecimalAsFloat = ValidateAs(float, lambda v: Decimal(str(v)))
ValidateDecimalAsInt = ValidateAs(int, lambda v: Decimal(v))
KeepStoredFloat = WrapValidator(partial(_keep_stored_decimal, integral=False))
KeepStoredInt = WrapValidator(partial(_keep_stored_decimal, integral=True))
ValidateStrAsISODateTime = ValidateAs(datetime, lambda dt: dt.isoformat())
ValidateStrAsUUID = ValidateAs(UUID, str)

ValidateDynamoFeatureStateValue = BeforeValidator(validate_dynamo_feature_state_value)
ValidateIdentityFeatureStatesList = AfterValidator(validate_identity_feature_states)
ValidateMultivariateFeatureValuesList = AfterValidator(
    validate_multivariate_feature_state_values
)
