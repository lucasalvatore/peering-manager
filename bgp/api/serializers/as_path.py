from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...models import ASPath

__all__ = ("ASPathSerializer", "NestedASPathSerializer")


class ASPathSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = ASPath
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "regexps",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]


class NestedASPathSerializer(WritableNestedSerializer):
    class Meta:
        model = ASPath
        fields = ["id", "url", "display_url", "display", "name", "slug"]
