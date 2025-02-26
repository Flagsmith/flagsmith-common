import typing

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db import models
from rest_framework import serializers

if typing.TYPE_CHECKING:
    from common.types import (
        Metadata,  # noqa: F401
        MetadataModelFieldRequirement,
        Organisation,
        Project,
    )


class MetadataSerializer(serializers.ModelSerializer["Metadata"]):
    class Meta:
        model = apps.get_model("metadata", "Metadata")
        fields = ("id", "model_field", "field_value")

    def validate(self, data: dict[str, typing.Any]) -> dict[str, typing.Any]:
        data = super().validate(data)
        if not data["model_field"].field.is_field_value_valid(data["field_value"]):
            raise serializers.ValidationError(
                f"Invalid value for field {data['model_field'].field.name}"
            )

        return data


class SerializerWithMetadata(serializers.Serializer[models.Model]):
    def get_organisation(
        self,
        validated_data: dict[str, typing.Any] | None = None,
    ) -> "Organisation":
        return self.get_project(validated_data).organisation

    def get_project(
        self,
        validated_data: dict[str, typing.Any] | None = None,
    ) -> "Project":
        raise NotImplementedError()

    def get_required_for_object(
        self,
        requirement: "MetadataModelFieldRequirement",
        data: dict[str, typing.Any],
    ) -> models.Model:
        model_name = requirement.content_type.model
        try:
            instance: models.Model = getattr(self, f"get_{model_name}")(data)
        except AttributeError:
            raise ValueError(
                f"`get_{model_name}_from_validated_data` method does not exist"
            )
        return instance

    def validate_required_metadata(
        self,
        data: dict[str, typing.Any],
    ) -> None:
        metadata = data.get("metadata", [])

        content_type = ContentType.objects.get_for_model(self.Meta.model)

        organisation = self.get_organisation(data)

        requirements: models.QuerySet["MetadataModelFieldRequirement"] = apps.get_model(
            "metadata", "MetadataModelFieldRequirement"
        ).objects.filter(
            model_field__content_type=content_type,
            model_field__field__organisation=organisation,
        )

        for requirement in requirements:
            required_for = self.get_required_for_object(requirement, data)
            if required_for.pk == requirement.object_id:
                if not any(
                    [
                        field["model_field"] == requirement.model_field
                        for field in metadata
                    ]
                ):
                    raise serializers.ValidationError(
                        {
                            "metadata": f"Missing required metadata field: {requirement.model_field.field.name}"
                        }
                    )

    def validate(
        self,
        data: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        data = super().validate(data)
        self.validate_required_metadata(data)
        return data

    class Meta:
        model: typing.Type[models.Model] = models.Model
