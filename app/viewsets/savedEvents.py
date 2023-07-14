from django.contrib.auth.models import User
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from app.models import *
from app.serializers import *

class SavedEventsViewset(viewsets.ModelViewSet):
    queryset = SavedEvent.objects.all()
    serializer_class = SavedEventSerializer