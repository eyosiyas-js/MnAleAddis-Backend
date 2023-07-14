from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models import *
from app.serializers import *
from app.scripts import extractToken,utils

class PromoCodeViewset(viewsets.ModelViewSet):

    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer

    def list(self,request,format = None):
        print("")