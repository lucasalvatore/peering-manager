from peering_manager.api.serializers import (
    PeeringManagerModelSerializer,
    WritableNestedSerializer,
)

from ...models import PrefixList

__all__ = ("NestedPrefixListSerializer", "PrefixListSerializer")


class PrefixListSerializer(PeeringManagerModelSerializer):
    class Meta:
        model = PrefixList
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "name",
            "slug",
            "description",
            "family",
            "prefixes",
            "local_context_data",
            "config_context",
            "tags",
            "created",
            "updated",
        ]


class NestedPrefixListSerializer(WritableNestedSerializer):
    class Meta:
        model = PrefixList
        fields = ["id", "url", "display_url", "display", "name", "slug", "family"]
