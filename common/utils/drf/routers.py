from functools import partial
from rest_framework.routers import DefaultRouter
from rest_framework.routers import Route as RestRoute

Route = partial(RestRoute, detail=False, initkwargs={})


class CustomSuffixRouter(DefaultRouter):
    def get_routes(self, viewset):
        routes = super().get_routes(viewset)

        create_route = Route(
            url=r'^{prefix}/create{trailing_slash}$',
            mapping={'post': 'create'},
            name='{basename}-create',
        )
        list_route = Route(
            url=r'^{prefix}/list{trailing_slash}$',
            mapping={'get': 'list'},
            name='{basename}-list',
        )

        return [*routes, create_route, list_route]
