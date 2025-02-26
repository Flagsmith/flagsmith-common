import typing

from django.apps import apps
from rest_framework import serializers

if typing.TYPE_CHECKING:
    from common.types import MultivariateFeatureStateValue  # noqa: F401


class MultivariateFeatureStateValueSerializer(
    serializers.ModelSerializer["MultivariateFeatureStateValue"]
):
    class Meta:
        model = apps.get_model("multivariate", "MultivariateFeatureStateValue")
        fields = (
            "id",
            "multivariate_feature_option",
            "percentage_allocation",
        )
