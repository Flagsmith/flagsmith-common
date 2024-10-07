import logging
from typing import Optional

from django.apps import apps
from django.conf import settings
from django.db import models
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ListSerializer
from rest_framework_recursive.fields import RecursiveField

logger = logging.getLogger(__name__)


class ConditionSerializer(serializers.ModelSerializer):
    delete = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = apps.get_model("segments", "Condition")
        fields = ("id", "operator", "property", "value", "description", "delete")

    def validate(self, attrs):
        super(ConditionSerializer, self).validate(attrs)
        if attrs.get("operator") != PERCENTAGE_SPLIT and not attrs.get("property"):
            raise ValidationError({"property": ["This field may not be blank."]})
        return attrs

    def to_internal_value(self, data):
        # convert value to a string - conversion to correct value type is handled elsewhere
        data["value"] = str(data["value"]) if "value" in data else None
        return super(ConditionSerializer, self).to_internal_value(data)


class RuleSerializer(serializers.ModelSerializer):
    delete = serializers.BooleanField(write_only=True, required=False)
    conditions = ConditionSerializer(many=True, required=False)
    rules = ListSerializer(child=RecursiveField(), required=False)

    class Meta:
        model = apps.get_model("segments", "SegmentRule")
        fields = ("id", "type", "rules", "conditions", "delete")


class SegmentSerializer(serializers.ModelSerializer, SerializerWithMetadata):
    rules = RuleSerializer(many=True)
    metadata = MetadataSerializer(required=False, many=True)

    class Meta:
        model = apps.get_model("segments", "Segment")
        fields = "__all__"

    def validate(self, attrs):
        attrs = super().validate(attrs)
        self.validate_required_metadata(attrs)
        if not attrs.get("rules"):
            raise ValidationError(
                {"rules": "Segment cannot be created without any rules."}
            )
        return attrs

    def get_project(self, validated_data: dict = None) -> models.Model:
        return validated_data.get("project") or apps.get_model(
            "projects", "Project"
        ).objects.get(id=self.context["view"].kwargs["project_pk"])

    def create(self, validated_data: dict) -> models.Model:
        Segment = apps.get_model("segments", "Segment")
        project = validated_data["project"]
        self.validate_project_segment_limit(project)

        rules_data = validated_data.pop("rules", [])
        metadata_data = validated_data.pop("metadata", [])
        self.validate_segment_rules_conditions_limit(rules_data)

        # create segment with nested rules and conditions
        segment = Segment.objects.create(**validated_data)
        self._update_or_create_segment_rules(
            rules_data, segment=segment, is_create=True
        )
        self._update_or_create_metadata(metadata_data, segment=segment)
        return segment

    def update(
        self, instance: models.Model, validated_data: dict[str, Any]
    ) -> models.Model:
        # use the initial data since we need the ids included to determine which to update & which to create
        rules_data = self.initial_data.pop("rules", [])
        metadata_data = validated_data.pop("metadata", [])
        self.validate_segment_rules_conditions_limit(rules_data)

        # Create a version of the segment now that we're updating.
        cloned_segment = instance.deep_clone()
        logger.info(
            f"Updating cloned segment {cloned_segment.id} for original segment {instance.id}"
        )

        try:
            self._update_segment_rules(rules_data, segment=instance)
            self._update_or_create_metadata(metadata_data, segment=instance)

            # remove rules from validated data to prevent error trying to create segment with nested rules
            del validated_data["rules"]
            response = super().update(instance, validated_data)
        except Exception:
            # Since there was a problem during the update we now delete the cloned segment,
            # since we no longer need a versioned segment.
            instance.refresh_from_db()
            instance.version = cloned_segment.version
            instance.save()
            cloned_segment.hard_delete()
            raise

        return response

    def validate_project_segment_limit(self, project: models.Model) -> None:
        if project.segments.count() >= project.max_segments_allowed:
            raise ValidationError(
                {
                    "project": "The project has reached the maximum allowed segments limit."
                }
            )

    def validate_segment_rules_conditions_limit(
        self, rules_data: dict[str, object]
    ) -> None:
        if self.instance and getattr(self.instance, "whitelisted_segment", None):
            return

        count = self._calculate_condition_count(rules_data)

        if count > settings.SEGMENT_RULES_CONDITIONS_LIMIT:
            raise ValidationError(
                {
                    "segment": f"The segment has {count} conditions, which exceeds the maximum "
                    f"condition count of {settings.SEGMENT_RULES_CONDITIONS_LIMIT}."
                }
            )

    def _calculate_condition_count(
        self,
        rules_data: dict[str, object],
    ) -> None:
        count: int = 0

        for rule_data in rules_data:
            child_rules = rule_data.get("rules", [])
            if child_rules:
                count += self._calculate_condition_count(child_rules)
            conditions = rule_data.get("conditions", [])
            for condition in conditions:
                if condition.get("delete", False) is True:
                    continue
                count += 1
        return count

    def _update_segment_rules(
        self, rules_data: dict, segment: Optional[models.Model] = None
    ) -> None:
        """
        Since we don't have a unique identifier for the rules / conditions for the update, we assume that the client
        passes up the new configuration for the rules of the segment and simply wipe the old ones and create new ones
        """
        Segment = apps.get_model("segments", "Segment")

        # traverse the rules / conditions tree - if no ids are provided, then maintain the previous behaviour (clear
        # existing rules and create the ones that were sent)
        # note: we do this to preserve backwards compatibility after adding logic to include the id in requests
        if not Segment.id_exists_in_rules_data(rules_data):
            segment.rules.set([])

        self._update_or_create_segment_rules(rules_data, segment=segment)

    def _update_or_create_segment_rules(
        self,
        rules_data: dict,
        segment: Optional[models.Model] = None,
        rule: Optional[models.Model] = None,
        is_create: bool = False,
    ) -> None:
        if all(x is None for x in {segment, rule}):
            raise RuntimeError("Can't create rule without parent segment or rule")

        for rule_data in rules_data:
            child_rules = rule_data.pop("rules", [])
            conditions = rule_data.pop("conditions", [])

            child_rule = self._update_or_create_segment_rule(
                rule_data, segment=segment, rule=rule
            )
            if not child_rule:
                # child rule was deleted
                continue

            self._update_or_create_conditions(
                conditions, child_rule, is_create=is_create
            )

            self._update_or_create_segment_rules(
                child_rules, rule=child_rule, is_create=is_create
            )

    def _update_or_create_metadata(
        self, metadata_data: dict, segment: Optional[models.Model] = None
    ) -> None:
        Metadata = apps.get_model("metadata", "Metadata")
        Segment = apps.get_model("segments", "Segment")
        if len(metadata_data) == 0:
            Metadata.objects.filter(object_id=segment.id).delete()
            return
        if metadata_data is not None:
            for metadata_item in metadata_data:
                metadata_model_field = metadata_item.pop("model_field", None)
                if metadata_item.get("delete"):
                    Metadata.objects.filter(model_field=metadata_model_field).delete()
                    continue

                Metadata.objects.update_or_create(
                    model_field=metadata_model_field,
                    defaults={
                        **metadata_item,
                        "content_type": ContentType.objects.get_for_model(Segment),
                        "object_id": segment.id,
                    },
                )

    @staticmethod
    def _update_or_create_segment_rule(
        rule_data: dict,
        segment: Optional[models.Model] = None,
        rule: Optional[models.Model] = None,
    ) -> Optional[models.Model]:
        SegmentRule = apps.get_model("segments", "SegmentRule")
        rule_id = rule_data.pop("id", None)
        if rule_data.get("delete"):
            SegmentRule.objects.filter(id=rule_id).delete()
            return

        segment_rule, _ = SegmentRule.objects.update_or_create(
            id=rule_id, defaults={"segment": segment, "rule": rule, **rule_data}
        )
        return segment_rule

    @staticmethod
    def _update_or_create_conditions(
        conditions_data: dict, rule: models.Model, is_create: bool = False
    ) -> None:
        Condition = apps.get_model("segments", "Condition")
        for condition in conditions_data:
            condition_id = condition.pop("id", None)
            if condition.get("delete"):
                Condition.objects.filter(id=condition_id).delete()
                continue

            Condition.objects.update_or_create(
                id=condition_id,
                defaults={**condition, "created_with_segment": is_create, "rule": rule},
            )