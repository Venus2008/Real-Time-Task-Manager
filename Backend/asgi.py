import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from notifications.middleware import JWTAuthMiddleware
from channels.auth import AuthMiddlewareStack


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Backend.settings")
django_asgi_app = get_asgi_application()
import notifications.routing
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
        URLRouter(notifications.routing.websocket_urlpatterns)
        )
    ),
})

