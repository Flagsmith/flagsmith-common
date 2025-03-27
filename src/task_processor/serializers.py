from rest_framework import serializers

from task_processor.types import MonitoringInfo


class MonitoringSerializer(serializers.Serializer[MonitoringInfo]):
    waiting = serializers.IntegerField(read_only=True)
