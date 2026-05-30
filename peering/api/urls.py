from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.PeeringRootView

router.register("autonomous-systems", views.AutonomousSystemViewSet)
router.register("bgp-groups", views.BGPGroupViewSet)
router.register("direct-peering-sessions", views.DirectPeeringSessionViewSet)
router.register("internet-exchanges", views.InternetExchangeViewSet)
router.register(
    "internet-exchange-peering-sessions", views.InternetExchangePeeringSessionViewSet
)
router.register("routing-policies", views.RoutingPolicyViewSet)
router.register("policy-terms", views.PolicyTermViewSet)
router.register("term-matches", views.TermMatchViewSet)
router.register("term-actions", views.TermActionViewSet)

app_name = "peering-api"
urlpatterns = router.urls
