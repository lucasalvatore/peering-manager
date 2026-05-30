import django_filters
from django.db.models import Q

from peering_manager.filtersets import PeeringManagerModelFilterSet

from ..enums import PrefixListFamily
from ..models import PrefixList

__all__ = ("PrefixListFilterSet",)


class PrefixListFilterSet(PeeringManagerModelFilterSet):
    family = django_filters.MultipleChoiceFilter(choices=PrefixListFamily)

    class Meta:
        model = PrefixList
        fields = ["id", "family"]

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(slug__icontains=value)
            | Q(description__icontains=value)
        )
