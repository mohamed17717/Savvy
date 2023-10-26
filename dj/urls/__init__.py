from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from .swagger import swagger_urls

urlpatterns = [
    path('bm/', include('App.urls', namespace='app')),
    path('users/', include('Users.urls', namespace='users')),
    path('api-auth/', include('rest_framework.urls')),
    path('admin/', admin.site.urls),
    path("__debug__/", include("debug_toolbar.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += swagger_urls
