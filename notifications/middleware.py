from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class TokenAuthMiddleware:
    """Proper ASGI middleware for token-based WebSocket auth."""
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        return lambda receive, send: self.__acall__(scope, receive, send)

    async def __acall__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = None

        if "token=" in query_string:
            token = query_string.split("token=")[-1].split("&")[0]

        if token:
            try:
                user, _ = TokenAuthentication().authenticate_credentials(token.encode())
                scope["user"] = user
            except AuthenticationFailed:
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope)(receive, send)
