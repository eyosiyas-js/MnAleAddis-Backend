from django.urls import path,re_path

from channels.auth import AuthMiddlewareStack
from .consumers import *

routes = [
    re_path(r'^ws/message/Attendee/(?P<user_id>\w+)$',AttendeeConsumer.as_asgi()),
    re_path(r'^ws/message/Organizer/(?P<user_id>\w+)$',OrganizerConsumer.as_asgi())
]