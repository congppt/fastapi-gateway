from starlette.authentication import AuthenticationBackend


class AuthMiddleware(AuthenticationBackend):
    def authenticate(self, request):
        if "Authorization" not in request.headers:
            return