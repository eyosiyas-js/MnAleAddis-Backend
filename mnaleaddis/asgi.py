"""
ASGI config for mnaleaddis project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mnaleaddis.settings')
django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter,URLRouter

import message.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket":AuthMiddlewareStack(
        URLRouter(
            message.routing.routes
        )
    )
})
