class HTTPError(Exception):

    def __init__(self, status_code, data=None, json=None):
        self.status_code = status_code
        self.data = data
        self.json = json
        super().__init__(
            'status code: {}, request data: {}, response body: {}'.format(
                status_code, data, json))


class ResponseError(HTTPError):
    pass


class ImproperlyConfigured(Exception):
    pass