class Response:
    def __init__(self, content=b"", json_data=None):
        self.content = content
        self._json = json_data or {}

    def json(self):
        return self._json


def get(url, *args, **kwargs):
    return Response()


def post(url, *args, **kwargs):
    return Response()


class Session:
    def get(self, *args, **kwargs):
        return get(*args, **kwargs)

    def post(self, *args, **kwargs):
        return post(*args, **kwargs)
