def get_flows():
    from .facebook import FacebookBookmarkHooks
    from .youtube import YoutubeBookmarkHooks
    from .instagram import InstagramBookmarkHooks

    return [
        FacebookBookmarkHooks,
        YoutubeBookmarkHooks,
        InstagramBookmarkHooks,
    ]


__all__ = ['get_flows']
