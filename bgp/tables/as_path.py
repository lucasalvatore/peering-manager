import django_tables2 as tables

from peering_manager.tables import PeeringManagerTable, columns

from ..models import ASPath

__all__ = ("ASPathTable",)


REGEXP_COUNT = "{{ record.regexps|length }}"


class ASPathTable(PeeringManagerTable):
    name = tables.Column(linkify=True)
    regexp_count = tables.TemplateColumn(
        template_code=REGEXP_COUNT, verbose_name="Expressions", orderable=False
    )
    tags = columns.TagColumn(url_name="bgp:aspath_list")

    class Meta(PeeringManagerTable.Meta):
        model = ASPath
        fields = ("pk", "name", "slug", "regexp_count", "tags", "actions")
        default_columns = ("pk", "name", "regexp_count", "actions")
