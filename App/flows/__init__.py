def get_flows():
    from .facebook import FacebookBookmarkHooks
    from .instagram import InstagramBookmarkHooks
    from .youtube import YoutubeBookmarkHooks

    return [
        FacebookBookmarkHooks,
        YoutubeBookmarkHooks,
        InstagramBookmarkHooks,
    ]


__all__ = ["get_flows"]
