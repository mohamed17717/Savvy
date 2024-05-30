from rest_framework.routers import DefaultRouter, Route


class CustomSuffixRouter(DefaultRouter):
    def get_routes(self, viewset):
        routes = super().get_routes(viewset)

        create_route = Route(
            url=r'^{prefix}/create{trailing_slash}$',
            mapping={'post': 'create'},
            name='{basename}-create',
            detail=False,
            initkwargs={}
        )
        list_route = Route(
            url=r'^{prefix}/list{trailing_slash}$',
            mapping={'get': 'list'},
            name='{basename}-list',
            detail=False,
            initkwargs={}
        )

        return [create_route, list_route, *routes]
