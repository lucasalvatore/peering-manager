from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import View

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

from ..filtersets import RoutingPolicyFilterSet
from ..forms import (
    RoutingPolicyBulkEditForm,
    RoutingPolicyFilterForm,
    RoutingPolicyForm,
)
from ..models import RoutingPolicy, RoutingPolicyVersion
from ..policy_history import record, restore
from ..tables import RoutingPolicyTable

__all__ = (
    "RoutingPolicyBulkDelete",
    "RoutingPolicyBulkEdit",
    "RoutingPolicyConfigContext",
    "RoutingPolicyDelete",
    "RoutingPolicyEdit",
    "RoutingPolicyList",
    "RoutingPolicySnapshot",
    "RoutingPolicyVersionRestore",
    "RoutingPolicyView",
)


@register_model_view(RoutingPolicy, name="list", path="", detail=False)
class RoutingPolicyList(ObjectListView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    filterset_form = RoutingPolicyFilterForm
    table = RoutingPolicyTable
    template_name = "peering/routingpolicy/list.html"


@register_model_view(RoutingPolicy)
class RoutingPolicyView(ObjectView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()

    def get_extra_context(self, request, instance):
        from ..policy_render import render_preview

        return {
            "terms": instance.terms.all(),
            "preview": render_preview(instance),
            "versions": instance.versions.all(),
        }


@register_model_view(model=RoutingPolicy, name="add", detail=False)
@register_model_view(model=RoutingPolicy, name="edit")
class RoutingPolicyEdit(ObjectEditView):
    queryset = RoutingPolicy.objects.all()
    form = RoutingPolicyForm


@register_model_view(RoutingPolicy, name="delete")
class RoutingPolicyDelete(ObjectDeleteView):
    permission_required = "peering.delete_routingpolicy"
    queryset = RoutingPolicy.objects.all()


@register_model_view(RoutingPolicy, name="bulk_edit", path="edit", detail=False)
class RoutingPolicyBulkEdit(BulkEditView):
    permission_required = "peering.change_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable
    form = RoutingPolicyBulkEditForm


@register_model_view(RoutingPolicy, name="bulk_delete", path="delete", detail=False)
class RoutingPolicyBulkDelete(BulkDeleteView):
    queryset = RoutingPolicy.objects.all()
    filterset = RoutingPolicyFilterSet
    table = RoutingPolicyTable


@register_model_view(RoutingPolicy, name="configcontext", path="config-context")
class RoutingPolicyConfigContext(ObjectConfigContextView):
    permission_required = "peering.view_routingpolicy"
    queryset = RoutingPolicy.objects.all()
    base_template = "peering/routingpolicy/_base.html"


@register_model_view(RoutingPolicy, name="snapshot", path="snapshot")
class RoutingPolicySnapshot(PermissionRequiredMixin, View):
    """Save the policy's current structured content as a version."""

    permission_required = "peering.change_routingpolicy"

    def post(self, request, pk):
        policy = get_object_or_404(RoutingPolicy, pk=pk)
        version = record(policy, comment=request.POST.get("comment", "").strip())
        messages.success(request, f"Saved version from {version.created:%Y-%m-%d %H:%M}.")
        return redirect(policy.get_absolute_url())


@register_model_view(
    RoutingPolicy, name="restore", path="versions/<int:version>/restore"
)
class RoutingPolicyVersionRestore(PermissionRequiredMixin, View):
    """Roll the policy back to a saved version."""

    permission_required = "peering.change_routingpolicy"

    def post(self, request, pk, version):
        policy = get_object_or_404(RoutingPolicy, pk=pk)
        target = get_object_or_404(
            RoutingPolicyVersion, pk=version, routing_policy=policy
        )
        restore(policy, target)
        messages.success(
            request, f"Restored to version from {target.created:%Y-%m-%d %H:%M}."
        )
        return redirect(policy.get_absolute_url())
