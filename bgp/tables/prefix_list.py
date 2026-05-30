import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from ..models import PrefixList

__all__ = ("PrefixListTable",)


PREFIX_COUNT = "{{ record.prefixes|length }}"


class PrefixListTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    family = tables.Column(verbose_name="Family")
    prefix_count = tables.TemplateColumn(
        template_code=PREFIX_COUNT, verbose_name="Prefixes", orderable=False
    )
    tags = columns.TagColumn(url_name="bgp:prefixlist_list")

    class Meta(PeeringManagerTable.Meta):
        model = PrefixList
        fields = ("pk", "name", "slug", "family", "prefix_count", "tags", "actions")
        default_columns = ("pk", "name", "family", "prefix_count", "actions")
