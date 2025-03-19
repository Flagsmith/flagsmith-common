import typing

from django.apps import apps
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from common.features.multivariate.serializers import (
    MultivariateFeatureStateValueSerializer,
)

if typing.TYPE_CHECKING:
    from common.types import FeatureSegment, FeatureStateValue  # noqa: F401


class FeatureStateValueSerializer(serializers.ModelSerializer["FeatureStateValue"]):
    class Meta:
        model = apps.get_model("features", "FeatureStateValue")
        fields = ("type", "string_value", "integer_value", "boolean_value")


class CreateSegmentOverrideFeatureSegmentSerializer(
    serializers.ModelSerializer["FeatureSegment"]
):
    class Meta:
        model = apps.get_model("features", "FeatureSegment")
        fields = ("id", "segment", "priority", "uuid")


class CreateSegmentOverrideFeatureStateSerializer(WritableNestedModelSerializer):
    feature_state_value = FeatureStateValueSerializer()
    feature_segment = CreateSegmentOverrideFeatureSegmentSerializer(
        required=False, allow_null=True
    )
    multivariate_feature_state_values = MultivariateFeatureStateValueSerializer(
        many=True, required=False
    )

    class Meta:
        model = apps.get_model("features", "FeatureState")
        fields = (
            "id",
            "feature",
            "enabled",
            "feature_state_value",
            "feature_segment",
            "deleted_at",
            "uuid",
            "created_at",
            "updated_at",
            "live_from",
            "environment",
            "identity",
            "change_request",
            "multivariate_feature_state_values",
        )

        read_only_fields = (
            "id",
            "deleted_at",
            "uuid",
            "created_at",
            "updated_at",
            "live_from",
            "environment",
            "identity",
            "change_request",
            "feature",
        )
