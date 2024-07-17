from django.apps import apps
from rest_framework import serializers


class MultivariateFeatureStateValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = apps.get_model("multivariate", "MultivariateFeatureStateValue")
        fields = (
            "id",
            "multivariate_feature_option",
            "percentage_allocation",
        )
