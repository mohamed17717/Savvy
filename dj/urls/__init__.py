from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from .swagger import swagger_urls

urlpatterns = [
    path('bm/', include('App.urls', namespace='app')),
    path('users/', include('Users.urls', namespace='users')),
]


if settings.DEBUG:
    urlpatterns += [
        path('api-auth/', include('rest_framework.urls')),
        path('admin/', admin.site.urls),

        # monitoring
        path('', include('django_prometheus.urls')),
        path('silk/', include('silk.urls', namespace='silk')),
        path('__debug__/', include('debug_toolbar.urls')),

        *swagger_urls,
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    ]
