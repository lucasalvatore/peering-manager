from peering_manager.views.generic import (
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
)
from utils.views import register_model_view

from ..filtersets import PolicyTermFilterSet
from ..forms import PolicyTermForm
from ..models import PolicyTerm
from ..tables import PolicyTermTable

__all__ = (
    "PolicyTermDelete",
    "PolicyTermEdit",
    "PolicyTermList",
)


@register_model_view(PolicyTerm, name="list", path="", detail=False)
class PolicyTermList(ObjectListView):
    permission_required = "peering.view_policyterm"
    queryset = PolicyTerm.objects.all()
    filterset = PolicyTermFilterSet
    table = PolicyTermTable
    template_name = "generic/object_list.html"


@register_model_view(model=PolicyTerm, name="add", detail=False)
@register_model_view(model=PolicyTerm, name="edit")
class PolicyTermEdit(ObjectEditView):
    queryset = PolicyTerm.objects.all()
    form = PolicyTermForm


@register_model_view(PolicyTerm, name="delete")
class PolicyTermDelete(ObjectDeleteView):
    permission_required = "peering.delete_policyterm"
    queryset = PolicyTerm.objects.all()
