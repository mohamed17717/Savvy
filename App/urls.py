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

    path('short/<str:uuid>/', views.BookmarkShortAPI.as_view(), name='bookmark_short_url'),

    path('', include(router.urls)),
]
