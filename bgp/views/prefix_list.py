from extras.views import ObjectConfigContextView
from peering_manager.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utils.views import register_model_view

from ..filtersets import PrefixListFilterSet
from ..forms import PrefixListBulkEditForm, PrefixListFilterForm, PrefixListForm
from ..models import PrefixList
from ..tables import PrefixListTable

__all__ = (
    "PrefixListBulkDelete",
    "PrefixListBulkEdit",
    "PrefixListConfigContext",
    "PrefixListDelete",
    "PrefixListEdit",
    "PrefixListList",
    "PrefixListView",
)


@register_model_view(PrefixList, name="list", path="", detail=False)
class PrefixListList(ObjectListView):
    permission_required = "bgp.view_prefixlist"
    queryset = PrefixList.objects.all()
    filterset = PrefixListFilterSet
    filterset_form = PrefixListFilterForm
    table = PrefixListTable
    template_name = "bgp/prefixlist/list.html"


@register_model_view(PrefixList)
class PrefixListView(ObjectView):
    permission_required = "bgp.view_prefixlist"
    queryset = PrefixList.objects.all()


@register_model_view(model=PrefixList, name="add", detail=False)
@register_model_view(model=PrefixList, name="edit")
class PrefixListEdit(ObjectEditView):
    queryset = PrefixList.objects.all()
    form = PrefixListForm
    template_name = "bgp/prefixlist/edit.html"

    def get_extra_context(self, request, instance):
        from ..enums import PrefixListMatchType

        # Param keys each match type takes, kept in sync with the preview renderer.
        type_params = {
            PrefixListMatchType.EXACT: [],
            PrefixListMatchType.LONGER: [],
            PrefixListMatchType.ORLONGER: [],
            PrefixListMatchType.UPTO: ["upto-length"],
            PrefixListMatchType.THROUGH: ["through-length"],
            PrefixListMatchType.PREFIX_LENGTH_RANGE: ["start-length", "end-length"],
            PrefixListMatchType.ADDRESS_MASK: ["mask-pattern"],
        }
        return {
            "editor_config": {
                "matchTypes": [c[0] for c in PrefixListMatchType.CHOICES],
                "typeParams": type_params,
            },
            "initial_prefixes": instance.prefixes if instance and instance.pk else [],
        }


@register_model_view(PrefixList, name="delete")
class PrefixListDelete(ObjectDeleteView):
    permission_required = "bgp.delete_prefixlist"
    queryset = PrefixList.objects.all()


@register_model_view(PrefixList, name="bulk_edit", path="edit", detail=False)
class PrefixListBulkEdit(BulkEditView):
    permission_required = "bgp.change_prefixlist"
    queryset = PrefixList.objects.all()
    filterset = PrefixListFilterSet
    table = PrefixListTable
    form = PrefixListBulkEditForm


@register_model_view(PrefixList, name="bulk_delete", path="delete", detail=False)
class PrefixListBulkDelete(BulkDeleteView):
    queryset = PrefixList.objects.all()
    filterset = PrefixListFilterSet
    table = PrefixListTable


@register_model_view(PrefixList, name="configcontext", path="config-context")
class PrefixListConfigContext(ObjectConfigContextView):
    permission_required = "bgp.view_prefixlist"
    queryset = PrefixList.objects.all()
    base_template = "bgp/prefixlist/_base.html"
