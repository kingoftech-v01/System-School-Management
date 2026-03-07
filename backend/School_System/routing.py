"""
ASGI routing for School_System project.
Routes HTTP and WebSocket connections to the appropriate handlers.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'School_System.settings')

# Initialize Django before importing anything else
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack  # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from django.urls import path  # noqa: E402

from anomaly_detection.consumers import AlertConsumer  # noqa: E402

websocket_urlpatterns = [
    path('ws/alerts/', AlertConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
