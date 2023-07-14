from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import *
from app.serializers import * 
from app.scripts import extractToken,utils,checkOrganizerPlan
from app.signals import signals

class ReviewViewSet(viewsets.ModelViewSet):

    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    # def create(self,request,format = None):
    #     return Response({
    #         "Success"
    #     })