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

from ..filtersets import ASPathFilterSet
from ..forms import ASPathBulkEditForm, ASPathFilterForm, ASPathForm
from ..models import ASPath
from ..tables import ASPathTable

__all__ = (
    "ASPathBulkDelete",
    "ASPathBulkEdit",
    "ASPathConfigContext",
    "ASPathDelete",
    "ASPathEdit",
    "ASPathList",
    "ASPathView",
)


@register_model_view(ASPath, name="list", path="", detail=False)
class ASPathList(ObjectListView):
    permission_required = "bgp.view_aspath"
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet
    filterset_form = ASPathFilterForm
    table = ASPathTable
    template_name = "bgp/aspath/list.html"


@register_model_view(ASPath)
class ASPathView(ObjectView):
    permission_required = "bgp.view_aspath"
    queryset = ASPath.objects.all()


@register_model_view(model=ASPath, name="add", detail=False)
@register_model_view(model=ASPath, name="edit")
class ASPathEdit(ObjectEditView):
    queryset = ASPath.objects.all()
    form = ASPathForm
    template_name = "bgp/aspath/edit.html"

    def get_extra_context(self, request, instance):
        return {
            "initial_regexps": instance.regexps if instance and instance.pk else [],
        }


@register_model_view(ASPath, name="delete")
class ASPathDelete(ObjectDeleteView):
    permission_required = "bgp.delete_aspath"
    queryset = ASPath.objects.all()


@register_model_view(ASPath, name="bulk_edit", path="edit", detail=False)
class ASPathBulkEdit(BulkEditView):
    permission_required = "bgp.change_aspath"
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet
    table = ASPathTable
    form = ASPathBulkEditForm


@register_model_view(ASPath, name="bulk_delete", path="delete", detail=False)
class ASPathBulkDelete(BulkDeleteView):
    queryset = ASPath.objects.all()
    filterset = ASPathFilterSet
    table = ASPathTable


@register_model_view(ASPath, name="configcontext", path="config-context")
class ASPathConfigContext(ObjectConfigContextView):
    permission_required = "bgp.view_aspath"
    queryset = ASPath.objects.all()
    base_template = "bgp/aspath/_base.html"
