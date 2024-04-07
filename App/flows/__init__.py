from abc import ABC, abstractmethod


class FlowController(ABC):
    DOMAIN = None

    @classmethod
    @abstractmethod
    def get_weighting_serializer(cls):
        pass

    @abstractmethod
    def run_flow(self):
        pass


def get_flows():
    from .facebook import FacebookBookmarkFlowController
    from .youtube import YoutubeBookmarkFlowController
    from .instagram import InstagramBookmarkFlowController

    return [
        FacebookBookmarkFlowController,
        YoutubeBookmarkFlowController,
        InstagramBookmarkFlowController
    ]


__all__ = ['get_flows']
