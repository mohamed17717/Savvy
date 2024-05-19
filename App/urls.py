from django.urls import path, include

from App import views

from common.utils.drf.routers import CustomSuffixRouter

router = CustomSuffixRouter()

router.register(r'file', views.BookmarkFileAPI, basename='file')
router.register(r'bookmark', views.BookmarkAPI, basename='bookmark')
router.register(r'tag', views.TagAPI, basename='tag')

app_name = 'app'

urlpatterns = [
    path('tags/list/', views.TagListAPI.as_view(), name='tag_list'),
    path('graph/', views.WordGraphNodeAPI.as_view(), name='node_graph'),

    path('short/<str:uuid>/', views.BookmarkShortAPI.as_view(), name='bookmark_short_url'),

    path('filter/choices/website/', views.BookmarkFilterChoices.Website.as_view(), name='filter_bookmark_choices_website'),
    path('filter/choices/topic/', views.BookmarkFilterChoices.Topic.as_view(), name='filter_bookmark_choices_topic'),
    path('', include(router.urls)),
]
