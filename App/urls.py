from django.urls import path, include

from App import views

from common.utils.drf.routers import CustomSuffixRouter

router = CustomSuffixRouter()

router.register(r'file', views.BookmarkFileAPI, basename='file')
router.register(r'cluster', views.ClusterAPI, basename='cluster_read')
router.register(r'bookmark', views.BookmarkAPI, basename='bookmark')
router.register(r'tag', views.TagAPI, basename='tag_read')

app_name = 'app'

urlpatterns = [
    path('tag/most-weighted/', views.TagMostWeightedListAPI.as_view(), name='tag_most_weighted'),
    path('tag/alias-name/<int:pk>/', views.TagUpdateAliasNameAPI.as_view(), name='tag_alias_name'),
    path('', include(router.urls)),
]
