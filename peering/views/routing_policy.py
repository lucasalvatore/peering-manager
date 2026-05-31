from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View

from devices.models import Router
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

from ..enums import RoutingPolicyType
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
    "RoutingPolicyByDeviceView",
    "RoutingPolicyConfigContext",
    "RoutingPolicyDelete",
    "RoutingPolicyEdit",
    "RoutingPolicyList",
    "RoutingPolicySnapshot",
    "RoutingPolicyVersionRestore",
    "RoutingPolicyView",
)


class RoutingPolicyByDeviceView(PermissionRequiredMixin, View):
    """
    Pick a device from a dropdown, then see the routing policies owned by it,
    split into import and export columns (bb_routing_policies-style browsing).
    """

    permission_required = "peering.view_routingpolicy"
    template_name = "peering/routingpolicy/by_device.html"

    def get(self, request):
        routers = Router.objects.all()
        router = None
        import_policies = RoutingPolicy.objects.none()
        export_policies = RoutingPolicy.objects.none()

        router_id = request.GET.get("router")
        if router_id:
            router = Router.objects.filter(pk=router_id).first()
        if router:
            owned = router.routing_policies.all()
            import_policies = owned.filter(
                type__in=[RoutingPolicyType.IMPORT, RoutingPolicyType.IMPORT_EXPORT]
            )
            export_policies = owned.filter(
                type__in=[RoutingPolicyType.EXPORT, RoutingPolicyType.IMPORT_EXPORT]
            )

        return render(
            request,
            self.template_name,
            {
                "routers": routers,
                "router": router,
                "import_policies": import_policies,
                "export_policies": export_policies,
            },
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
