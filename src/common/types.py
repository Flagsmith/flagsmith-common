import typing

if typing.TYPE_CHECKING:
    from django.contrib.contenttypes.models import ContentType
    from django.db import models

    FeatureStateValue: typing.TypeAlias = models.Model
    FeatureSegment: typing.TypeAlias = models.Model
    Condition: typing.TypeAlias = models.Model
    MultivariateFeatureStateValue: typing.TypeAlias = models.Model
    Metadata: typing.TypeAlias = models.Model
    Organisation: typing.TypeAlias = models.Model

    class SoftDeleteExportableModel(models.Model):
        def hard_delete(self) -> None: ...

    class Segment(SoftDeleteExportableModel):
        id: int
        version: int | None
        rules = models.ForeignKey("Rule", on_delete=models.CASCADE)

        def deep_clone(self) -> "Segment": ...

    class Rule(models.Model):
        def get_segment(self) -> Segment: ...

    class SegmentRule(Rule):
        pass

    class Project(models.Model):
        organisation: "Organisation"
        max_segments_allowed: int

    class MetadataField(models.Model):
        name: str
        organisation: "Organisation"

    class MetadataModelField(models.Model):
        field: "MetadataField"
        content_type: ContentType

    class MetadataModelFieldRequirement(models.Model):
        model_field: "MetadataModelField"
        object_id: int
        content_type: ContentType
