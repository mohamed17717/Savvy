from django.urls import path, include

from App import views

from common.utils.drf.routers import CustomSuffixRouter

router = CustomSuffixRouter()

router.register(r'file', views.BookmarkFileAPI, basename='file')
router.register(r'cluster', views.ClusterAPI, basename='cluster_read')
router.register(r'bookmark', views.BookmarkAPI, basename='bookmark')

app_name = 'app'

urlpatterns = [
    path('', include(router.urls)),
]
