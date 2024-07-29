from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('api/bm/', include('App.urls', namespace='app')),
    path('api/users/', include('Users.urls', namespace='users')),
]


if settings.DEBUG:
    from .swagger import swagger_urls

    urlpatterns += [
        path('api-auth/', include('rest_framework.urls')),
        path('admin/', admin.site.urls),

        # monitoring
        path('__debug__/', include('debug_toolbar.urls')),

        *swagger_urls,
        *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
        *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    ]
