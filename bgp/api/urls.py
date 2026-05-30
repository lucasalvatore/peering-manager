from peering_manager.api.routers import PeeringManagerRouter

from . import views

router = PeeringManagerRouter()
router.APIRootView = views.BGPRootView

router.register("as-paths", views.ASPathViewSet)
router.register("communities", views.CommunityViewSet)
router.register("prefix-lists", views.PrefixListViewSet)
router.register("relationships", views.RelationshipViewSet)

app_name = "bgp-api"
urlpatterns = router.urls
