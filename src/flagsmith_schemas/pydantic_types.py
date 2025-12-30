from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AfterValidator, BeforeValidator, ValidateAs

from flagsmith_schemas.validators import (
    validate_dynamo_feature_state_value,
    validate_identity_feature_states,
    validate_multivariate_feature_state_values,
)

ValidateDecimalAsFloat = ValidateAs(float, lambda v: Decimal(str(v)))
ValidateDecimalAsInt = ValidateAs(int, lambda v: Decimal(v))
ValidateStrAsISODateTime = ValidateAs(datetime, lambda dt: dt.isoformat())
ValidateStrAsUUID = ValidateAs(UUID, str)

ValidateDynamoFeatureStateValue = BeforeValidator(validate_dynamo_feature_state_value)
ValidateIdentityFeatureStatesList = AfterValidator(validate_identity_feature_states)
ValidateMultivariateFeatureValuesList = AfterValidator(
    validate_multivariate_feature_state_values
)
