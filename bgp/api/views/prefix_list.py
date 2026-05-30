from peering_manager.api.viewsets import PeeringManagerModelViewSet

from ...filtersets import PrefixListFilterSet
from ...models import PrefixList
from ..serializers import PrefixListSerializer

__all__ = ("PrefixListViewSet",)


class PrefixListViewSet(PeeringManagerModelViewSet):
    queryset = PrefixList.objects.all()
    serializer_class = PrefixListSerializer
    filterset_class = PrefixListFilterSet
