"""
ASGI config for School_System project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "School_System.settings")

# Import the Channels routing application which handles both HTTP and WebSocket
from School_System.routing import application  # noqa: E402, F401
