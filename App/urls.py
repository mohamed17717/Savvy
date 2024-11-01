from django.urls import include, path

from App import views
from common.utils.drf.routers import CustomSuffixRouter

router = CustomSuffixRouter()

router.register(r"file", views.BookmarkFileAPI, basename="file")
router.register(r"bookmark", views.BookmarkAPI, basename="bookmark")
router.register(r"tag", views.TagAPI, basename="tag")

app_name = "app"

urlpatterns = [
    path("tags/list/", views.TagListAPI.as_view(), name="tag_list"),
    path(
        "filter/choices/website/",
        views.BookmarkFilterChoices.Website.as_view(),
        name="filter_bookmark_choices_website",
    ),
    path(
        "filter/choices/topic/",
        views.BookmarkFilterChoices.Topic.as_view(),
        name="filter_bookmark_choices_topic",
    ),
    path("", include(router.urls)),
]
