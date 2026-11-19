import typing

from django.apps import apps
from rest_framework import serializers

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
