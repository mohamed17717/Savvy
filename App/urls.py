from django.urls import path, include

from App import views

from common.utils.drf.routers import CustomSuffixRouter

router = CustomSuffixRouter()

router.register(r'file', views.BookmarkFileUploadAPI, basename='file')

app_name = 'app'

urlpatterns = [
    path('', include(router.urls)),
]
