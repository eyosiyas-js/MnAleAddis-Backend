from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from app.models import *
from app.serializers import *
from app.scripts import extractToken

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def create(self,request,format=None):
        admin = extractToken.checkAdminToken(request.headers)

        if 'tag' not in request.data: raise ValueError("Tag is required")

        if Tag.objects.filter(tag=request.data['tag']).exists(): raise ValueError("Tag already exists")
        Tag.objects.create(
            tag= request.data['tag']
        )
        return Response({
            "status":True,
            "message":"Successfully created the tag"
        })