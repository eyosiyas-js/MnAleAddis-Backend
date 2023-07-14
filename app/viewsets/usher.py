from django.utils import timezone

from rest_framework import status,viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend


from app.models import *
from app.serializers import * 
from app.scripts import extractToken,utils,checkOrganizerPlan,notifyAttendees,telebirr
from app.signals import signals

class UsherViewset(viewsets.ModelViewSet):

    queryset = Usher.objects.all()
    serializer_class = UsherSerializer

    def create(self,request, format = None):
        if 'code' not in request.data.keys():
            raise ValueError("Code is required")
        
        checkUsher = Usher.objects.filter(code = request.data['code'])

        if not checkUsher.exists():
            return Response({"success":False},status.HTTP_401_UNAUTHORIZED)

        type = ''
        if checkUsher[0].event.normalPrice != 0 or checkUsher[0].event.vipPrice !=0 or checkUsher[0].event.vvipPrice != 0:
            type = 'Booking'
        else:
            type = 'RSVP'

        return Response({
            "success":True,
            "data":{
                "event_name": checkUsher[0].event.name,
                "type":type,
                "start_date": checkUsher[0].event.startDate,
                "end_date": checkUsher[0].event.endDate,
                "normal_price": checkUsher[0].event.normalPrice,
                "vip_price": checkUsher[0].event.vipPrice,
                "vvip_price": checkUsher[0].event.vvipPrice
            }
        })
    
    @action(detail = False, methods=['PUT'])
    def scanPrivateEventCode(self , request , pk = None , format = None):

        if 'usher_code' not in request.data.keys():
            raise ValueError("Usher's Code is required")
        
        if not 'rsvp_code' in request.data.keys():
            raise ValueError("All required values must be input")
        
        checkUsher = Usher.objects.filter(code = request.data['usher_code'])

        if not checkUsher.exists():
            return Response({"success":False},status.HTTP_401_UNAUTHORIZED)
        
        checkEvent = checkUsher[0].event
        print(checkEvent)

        checkReservation = Reservation.objects.filter(pk = request.data['rsvp_code'])

        print(checkReservation)
        if not checkReservation.exists():
            return Response({
                "sucess":False,
                "message":"Succesfully scanned the QR Code",
                "action":"Reservation does not exist"
            },status.HTTP_400_BAD_REQUEST)

        if checkReservation[0].pending_status != True:
            return Response({
                "sucess":False,
                "message":"Succesfully scanned the QR Code",
                "action":"User has already attended the event"
            },status.HTTP_400_BAD_REQUEST)

        checkReservation.update(
            pending_status = False
        )

        return Response({
            "success":True,
            "message":"Successfully scanned the QR code",
            "action":"User can attend the event"
        })
        
    @action(detail=False,methods=['PUT'])
    def scanQRCode(self,request,pk=None,format=None):

        if 'usher_code' not in request.data.keys():
            raise ValueError("Usher's Code is required")
        
        if not 'booking_code' in request.data.keys():
            raise ValueError("All required values must be input")

        checkUsher = Usher.objects.filter(code = request.data['usher_code'])

        if not checkUsher.exists():
            return Response({"success":False},status.HTTP_401_UNAUTHORIZED)

        checkEvent = checkUsher[0].event
        
        checkBooking = Booking.objects.filter(code=request.data['booking_code'])
        if not checkBooking.exists():
            raise ValueError("Booking does not exist")
        
        if checkBooking[0].has_attended == True:
            return Response({
                "Success":False,
                "message":"Succesfully Scanned the QR Code",
                "action":"User has already attended the event"
            },status.HTTP_400_BAD_REQUEST)

        if checkBooking[0].event.pk != checkEvent[0].pk:
            raise ValueError("Invalid booking code")
        
        if checkBooking[0].event.startDate > timezone.now():
            raise ValueError("Event not started yet")

        if checkBooking[0].event.endDate < timezone.now():
            raise ValueError("Event has already ended")
        
        checkReservation = Reservation.objects.filter(attendee = checkBooking[0].attendee,event = checkEvent[0])
        
        if checkReservation.exists():
            checkReservation.update(
                pending_status = False
            )
        
        max_no_attendees = checkEvent[0].maxNoOfAttendees

        checkEvent.update(
            maxNoOfAttendees = max_no_attendees - checkBooking[0].number
        )

        checkBooking.update(
            has_attended = True
        )

        signals.add_to_wallet.send(sender = "user-booking-success",attendee = checkBooking[0].attendee,action='user-booking-success')

        return Response({
            "Success":True,
            "message":"Succesfully Scanned the QR Code",
            "action":"User can attend the event"
        })
    
    @action(detail = False,methods=['PUT'])
    def scanReservationCode(self, request, pk = None, format = None):
        if not 'usher_code' or not 'rsvp_code' in request.data.keys():
            raise ValueError("Usher's Code is required")

        checkUsher = Usher.objects.filter(code = request.data['usher_code'])

        if not checkUsher.exists():
            return Response({"success":False},status.HTTP_401_UNAUTHORIZED)

        checkEvent = checkUsher[0].event

        checkReservation = Reservation.objects.filter(pk = request.data['rsvp_code'],event = checkEvent)
        print(checkReservation)

        if not checkReservation.exists():
            return Response({
                "sucess":False,
                "message":"Succesfully scanned the QR Code",
                "action":"Reservation does not exist"
            },status.HTTP_400_BAD_REQUEST)
        
        if checkReservation[0].pending_status != True:
            return Response({
                "sucess":False,
                "message":"Succesfully scanned the QR Code",
                "action":"User has already attended the event"
            },status.HTTP_400_BAD_REQUEST) 
        
        checkReservation.update(
            pending_status = False
        )

        return Response({
            "success":True,
            "message":"Successfully scanned the QR code",
            "action":"User can attend the event"
        })