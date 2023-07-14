from datetime import datetime
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from app.models import *
from app.serializers import * 

from django.utils import timezone

class EventSeenViewSet(viewsets.ModelViewSet):

    queryset = EventSeen.objects.all()
    serializer_class = EventSeenSerialzier