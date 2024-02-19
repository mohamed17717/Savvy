from django.urls import path, include

from App import views

from common.utils.drf.routers import CustomSuffixRouter

router = CustomSuffixRouter()

router.register(r'file', views.BookmarkFileAPI, basename='file')
router.register(r'bookmark', views.BookmarkAPI, basename='bookmark')
router.register(r'cluster', views.ClusterAPI, basename='cluster')
router.register(r'tag', views.TagAPI, basename='tag')

app_name = 'app'

urlpatterns = [
    path('clusters/all/', views.ClusterFullListAPI.as_view(), name='clusters_list'),
    path('tags/list/', views.TagListAPI.as_view(), name='tag_list'),

    path('', include(router.urls)),
]
