import redis
import json

from dj.settings import REDIS_HOST, REDIS_PORT


class BookmarkRedisPublisher:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    class Types:
        FILE_UPLOAD = 1
        BOOKMARK_CHANGE = 2

    def __init__(self, user):
        self.user = user
        self.CHANNEL_NAME = 'bookmarks_progress'

    def publish(self, data):
        _type = self.Types.FILE_UPLOAD
        if 'bookmark_id' in data.keys():
            _type = self.Types.BOOKMARK_CHANGE

        payload = {
            'user_id': self.user.id,
            'type': _type,
            'data': data
        }
        self.redis_client.publish(self.CHANNEL_NAME, json.dumps(payload))
