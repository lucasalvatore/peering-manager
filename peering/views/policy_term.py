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


MATCH_TYPES = [
    "prefix-list",
    "community",
    "as-path",
    "protocol",
    "family",
    "neighbor",
    "origin",
    "route-type",
    "interface",
]
ACTION_TYPES = [
    "local-preference",
    "metric",
    "as-path-prepend",
    "community-add",
    "community-remove",
    "origin",
    "next-hop",
    "tag",
    "damping",
]
PROTOCOLS = ["bgp", "static", "direct", "ospf", "ospf3", "isis", "aggregate", "local"]


@register_model_view(model=PolicyTerm, name="add", detail=False)
@register_model_view(model=PolicyTerm, name="edit")
class PolicyTermEdit(ObjectEditView):
    queryset = PolicyTerm.objects.all()
    form = PolicyTermForm
    template_name = "peering/policyterm/edit.html"

    def get_extra_context(self, request, instance):
        from bgp.models import ASPath, Community, PrefixList

        editor_config = {
            "matchTypes": MATCH_TYPES,
            "actionTypes": ACTION_TYPES,
            "protocols": PROTOCOLS,
            # Match/action kinds whose values are picked from named objects.
            "objectMatchTypes": ["prefix-list", "community", "as-path"],
            "communityActionTypes": ["community-add", "community-remove"],
            "objects": {
                "prefix-list": list(
                    PrefixList.objects.values_list("name", flat=True)
                ),
                "community": list(Community.objects.values_list("name", flat=True)),
                "as-path": list(ASPath.objects.values_list("name", flat=True)),
            },
        }
        initial_matches, initial_actions = [], []
        if instance and instance.pk:
            initial_matches = [
                {"match_type": m.match_type, "values": m.values}
                for m in instance.matches.all()
            ]
            initial_actions = [
                {"action_type": a.action_type, "value": a.value}
                for a in instance.actions.all()
            ]
        return {
            "editor_config": editor_config,
            "initial_matches": initial_matches,
            "initial_actions": initial_actions,
        }


@register_model_view(PolicyTerm, name="delete")
class PolicyTermDelete(ObjectDeleteView):
    permission_required = "peering.delete_policyterm"
    queryset = PolicyTerm.objects.all()
