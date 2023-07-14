from django.contrib.auth.models import User
from django.db.models import Count

from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.scripts import utils
from app.models import *
from app.serializers import *

class OrganizerFollowingViewSet(viewsets.ModelViewSet):

    queryset = OrganizerFollowing.objects.all()
    serializer_class = OrganizerFollowingSerializer

    @action(detail=False,methods=['GET'])
    def eventsByManyFollowers(self,request,format=None):

        most_common = OrganizerFollowing.objects.annotate(mc = Count('organizer')).order_by('-mc')[0].mc
        print(most_common)

        organizer = OrganizerFollowing.objects.get(pk = most_common)
        eventsByTopFollowing = Event.objects.filter(createdBy_id= organizer.organizer)

        return Response({
            "success":True,
            "data":utils.eventFormatter(eventsByTopFollowing)
        })