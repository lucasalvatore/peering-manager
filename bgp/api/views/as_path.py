from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import ASPathFilterSet
from ...models import ASPath
from ..serializers import ASPathSerializer

__all__ = ("ASPathViewSet",)


class ASPathViewSet(PeeringManagerModelViewSet):
    queryset = ASPath.objects.all()
    serializer_class = ASPathSerializer
    filterset_class = ASPathFilterSet
