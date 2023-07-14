from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models import *
from app.serializers import *
from app.scripts import extractToken

class PaymentPlanViewSet(viewsets.ModelViewSet):

    queryset = PaymentPlan.objects.all()
    serializer_class = PaymentPlanSerialzier

    def create(self, request, *args, **kwargs):

        admin = extractToken.checkAdminToken(request.headers)
        return super().create(request, *args, **kwargs)
    
    @action(detail=True,methods=['PUT'])
    def choosePlan(self,request,pk=None,format=None):
        
        organizer = extractToken.checkOrganizerToken(request.headers)

        checkPlan = PaymentPlan.objects.filter(pk=pk)
        
        checkOrganizerPlan = OrganizerDetail.objects.filter(organizer = organizer)
        
        if not checkPlan.exists():
            raise ValueError("Plan does not exist")
        
        if not checkOrganizerPlan.exists():
            OrganizerDetail.objects.create(
                organizer = organizer,
                payment_plan = checkPlan[0]
            )
        
            return Response({
                "Success":True,
                "message":"Succesfully chosen the payment plan " + str(checkPlan[0].name)
            })
        
        else:
            checkOrganizerPlan.update(
                payment_plan = checkPlan[0]
            ) 

            return Response({
                "status":True,
                "message":"Succesfully updated the payment plan to " + str(checkPlan[0].name)
            })