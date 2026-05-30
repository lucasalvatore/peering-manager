from django.urls import include, path

from utils.urls import get_model_urls

from . import views  # noqa: F401

app_name = "bgp"
urlpatterns = [
    # Communities
    path(
        "communities/",
        include(get_model_urls(app_label="bgp", model_name="community", detail=False)),
    ),
    path(
        "communities/<int:pk>/",
        include(get_model_urls(app_label="bgp", model_name="community")),
    ),
    # Prefix lists
    path(
        "prefix-lists/",
        include(
            get_model_urls(app_label="bgp", model_name="prefixlist", detail=False)
        ),
    ),
    path(
        "prefix-lists/<int:pk>/",
        include(get_model_urls(app_label="bgp", model_name="prefixlist")),
    ),
    # AS paths
    path(
        "as-paths/",
        include(get_model_urls(app_label="bgp", model_name="aspath", detail=False)),
    ),
    path(
        "as-paths/<int:pk>/",
        include(get_model_urls(app_label="bgp", model_name="aspath")),
    ),
    # Relationships
    path(
        "relationships/",
        include(
            get_model_urls(app_label="bgp", model_name="relationship", detail=False)
        ),
    ),
    path(
        "relationships/<int:pk>/",
        include(get_model_urls(app_label="bgp", model_name="relationship")),
    ),
]
