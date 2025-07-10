from django.contrib.auth.models import AnonymousUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class TokenAuthMiddleware:
    """ASGI-compliant middleware for token-based WebSocket auth."""
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, scope):
        async def asgi(receive, send):
            # Extract token from query string
            query_string = scope.get("query_string", b"").decode()
            token = None

            if "token=" in query_string:
                token = query_string.split("token=")[-1].split("&")[0]

            # Try to authenticate using DRF's TokenAuthentication
            if token:
                try:
                    user, _ = TokenAuthentication().authenticate_credentials(token.encode())
                    scope["user"] = user
                except AuthenticationFailed:
                    scope["user"] = AnonymousUser()
            else:
                scope["user"] = AnonymousUser()

            return await self.inner(scope)(receive, send)

        return asgi
