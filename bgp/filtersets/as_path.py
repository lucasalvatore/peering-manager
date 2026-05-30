from django.db.models import Q

from peering_manager.filtersets import PeeringManagerModelFilterSet

from ..models import ASPath

__all__ = ("ASPathFilterSet",)


class ASPathFilterSet(PeeringManagerModelFilterSet):
    class Meta:
        model = ASPath
        fields = ["id"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(slug__icontains=value)
            | Q(description__icontains=value)
        )
