from starlette.authentication import AuthenticationBackend, AuthenticationError
from starlette.requests import HTTPConnection

from constants.env import AUTH_SCHEME


class AuthMiddleware(AuthenticationBackend):
    def authenticate(self, conn: HTTPConnection):
        if "Authorization" not in conn.headers:
            raise AuthenticationError('Missing Authorization header')
        scheme, token = conn.headers["Authorization"].split(" ")
        if scheme != AUTH_SCHEME:
            raise AuthenticationError('Authorization scheme does not match')

