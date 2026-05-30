from peering_manager.api.serializers import WritableNestedSerializer

from ..models import (
    AutonomousSystem,
    BGPGroup,
    DirectPeeringSession,
    InternetExchange,
    InternetExchangePeeringSession,
    PolicyTerm,
    RoutingPolicy,
    TermAction,
    TermMatch,
)

__all__ = (
    "NestedAutonomousSystemSerializer",
    "NestedBGPGroupSerializer",
    "NestedDirectPeeringSessionSerializer",
    "NestedInternetExchangePeeringSessionSerializer",
    "NestedInternetExchangeSerializer",
    "NestedPolicyTermSerializer",
    "NestedRoutingPolicySerializer",
    "NestedTermActionSerializer",
    "NestedTermMatchSerializer",
)


class NestedAutonomousSystemSerializer(WritableNestedSerializer):
    class Meta:
        model = AutonomousSystem
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "asn",
            "name",
            "ipv6_max_prefixes",
            "ipv4_max_prefixes",
        ]


class NestedBGPGroupSerializer(WritableNestedSerializer):
    class Meta:
        model = BGPGroup
        fields = ["id", "url", "display_url", "display", "name", "slug", "status"]


class NestedDirectPeeringSessionSerializer(WritableNestedSerializer):
    class Meta:
        model = DirectPeeringSession
        fields = ["id", "url", "display_url", "display", "ip_address", "status"]


class NestedInternetExchangeSerializer(WritableNestedSerializer):
    class Meta:
        model = InternetExchange
        fields = ["id", "url", "display_url", "display", "name", "slug", "status"]


class NestedInternetExchangePeeringSessionSerializer(WritableNestedSerializer):
    class Meta:
        model = InternetExchangePeeringSession
        fields = [
            "id",
            "url",
            "display_url",
            "display",
            "ip_address",
            "status",
            "is_route_server",
        ]


class NestedRoutingPolicySerializer(WritableNestedSerializer):
    class Meta:
        model = RoutingPolicy
        fields = ["id", "url", "display_url", "display", "name", "slug", "type"]


class NestedPolicyTermSerializer(WritableNestedSerializer):
    class Meta:
        model = PolicyTerm
        fields = ["id", "url", "display_url", "display", "name", "sequence", "action"]


class NestedTermMatchSerializer(WritableNestedSerializer):
    class Meta:
        model = TermMatch
        fields = ["id", "url", "display_url", "display", "match_type", "values"]


class NestedTermActionSerializer(WritableNestedSerializer):
    class Meta:
        model = TermAction
        fields = ["id", "url", "display_url", "display", "action_type", "value"]
