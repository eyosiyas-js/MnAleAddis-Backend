from datetime import datetime
from io import BytesIO

from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import qrcode
import qrcode.image.svg

import cloudinary,cloudinary.uploader,cloudinary.api

from app.models import *
from app.serializers import *
from app.scripts import utils

from app.scripts import extractToken,checkOrganizerPlan

class GraduationEventViewSet(viewsets.ModelViewSet):

    queryset = GraduationEvent.objects.all()
    serializer_class = GraduationEventSerializer
    
    def create(self, request, *args, **kwargs):
        
        organizer = extractToken.checkOrganizerToken(request.headers)

        plan = checkOrganizerPlan.checkOrganizerPlan(organizer)

        names = ('name','price','phones','venue','description','startDate','location','maxNoOfAttendees','minPercentageToPay')
        if not all(name in request.data.keys() for name in names):
            raise ValueError("All required fields must be input")
        
        #check the request body is not of string value
        if isinstance(request.data,str):
            raise ValueError("All required fields must be input")
        #check the phones values is a list
        if not isinstance(request.data['phones'],list):
            raise ValueError("Phones must be an array")
        
        if not utils.is_datetime(datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M')):
            raise ValueError("Invalid start date format")
        if datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M') < datetime.now():
            raise ValueError("Start Date can not be before the Current time and date")
        
        if not type(request.data['maxNoOfAttendees'] == int):
            raise ValueError("Attendee must be an integer")
        if not request.data['name'] or not request.data['description']:
            raise ValueError("All required fields must be input")
        if not type(request.data['price']) == int and not type(request.data['price']) == float:
            raise ValueError("Price must be a number")

        if 'venue' in request.data:
            if not request.data['venue']:
                raise ValueError("Venue can not be empty")
        if request.data['price'] < 0:
            raise ValueError("Price can not be less than 0")

        if request.data['minPercentageToPay'] < 0 or request.data['minPercentageToPay'] > 100:
            raise ValueError("minPercentageToPay must be in allowed range")
        
        GraduationEvent.objects.create(
            name = request.data['name'],
            price = request.data['price'],
            description = request.data['description'],
            startDate = request.data['startDate'],
            phones = request.data['phones'],
            maxNoOfAttendees = request.data['maxNoOfAttendees'],
            venue = request.data['venue'],
            location = request.data['location'],
            createdBy = organizer,
            minPercentageToPay = request.data['minPercentageToPay'],
            eventkey = utils.randomCodeGenerator(20)
        )
        # data = {}
        
        # data['name'] = request.data['name']
        # data['price'] = request.data['minPercentageToPay']
        # data['description'] = request.data['description']
        # data['startDate'] = request.data['startDate']
        # data['phones'] = request.data['phones']
        # data['maxNoOfAttendees'] = request.data['maxNoOfAttendees']
        # data['venue'] = request.data['venue']
        # data['location'] = request.data['location']
        # data['createdBy'] = organizerSerializer.data['url']
        # data['minPercentageToPay'] = request.data['minPercentageToPay'],
        # data['eventkey'] = utils.randomCodeGenerator(20)

        # print(isinstance(request.data['minPercentageToPay'],int))
        # serializer = GraduationEventSerializer(data = data,context ={'request':request})
        # if not serializer.is_valid():
        #     print(serializer.errors)
        #     return Response({
        #         "success":False,
        #     })        

        # serializer.save()

        return Response({
            "success":True,
            "message":"Successfully Created the Event",
            # "data":serializer.data
        })
    
    @action(detail=False,methods=['GET'])
    def getMyGraduationEvents(self,request,format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvents = GraduationEvent.objects.filter(createdBy = organizer)

        if checkEvents.exists():
            return Response({
                "success":True,
                "data":utils.graduationEventFormatter(checkEvents)
            })
        else:

            return Response({
                "success":True,
                "data":[]
            })
    
    @action(detail=False,methods=['GET'],url_path='getGraduationEventWithCode/(?P<key>[A-z0-9]+)')
    def getGraduationEventWithCode(self,request,format = None, *args, **kwargs):
        attendee = extractToken.checkAttendeeToken(request.headers)

        getEvent = GraduationEvent.objects.filter(eventkey = kwargs['key'])
        if not getEvent.exists():
            raise ValueError("Event not found.")

        return Response({
            "success":True,
            "data":utils.graduationEventFormatter(getEvent)[0]
        })
    
    @action(detail=False,methods=['PUT'],url_path='bookGraduationEvent/(?P<key>[A-z0-9]+)')
    def bookGraduationEvent(self,request,format = None, *args, **kwargs):
        attendee = extractToken.checkAttendeeToken(request.headers)

        if 'amount' not in request.data.keys():
            raise ValueError("amount is a required property.")

        amount = request.data['amount']
        if not isinstance(amount,int) and not isinstance(amount,float):
            raise ValueError("amount must be a number.")

        getEvent = GraduationEvent.objects.filter(eventkey = kwargs['key'])
        if not getEvent.exists():
            raise ValueError("Event not found.")
        
        checkBooking = GraduationBooking.objects.filter(attendee = attendee,graduationEvent = getEvent[0])
        if not checkBooking.exists():

            minimumAllowedPrice = round(getEvent[0].price * (getEvent[0].minPercentageToPay / 100),2)

            if amount > getEvent[0].price or amount < minimumAllowedPrice:
                raise ValueError("The allowed amount to pay for the event is between "+str(minimumAllowedPrice)+" and "+str(getEvent[0].price))
            else:
                leftPayment = getEvent[0].price - amount 
                print(round((amount / getEvent[0].price) * 100,2))
                code = utils.randomCodeGenerator(10)

                context = {}
                factory = qrcode.image.svg.SvgImage
                img = qrcode.make(code,image_factory=factory,box_size=40)
                
                stream = BytesIO()
                img.save(stream)

                # #This is the part where the payment Integration will be made
                # #
                uploadedfile = cloudinary.uploader.upload(
                    stream.getvalue(), 
                    folder = "MinAleAddis/QRCodes/GraduationEvents/", 
                    public_id = code+'qrcode',
                    overwrite = True,  
                    resource_type = "image"
                )

                GraduationBooking.objects.create(
                    attendee = attendee,
                    graduationEvent = getEvent[0],
                    percentagePayed = round((amount / getEvent[0].price) * 100,2),
                    code = code,
                    qrcode = uploadedfile['url']
                )

                return Response({
                    "success":True,
                    "message":"Successfully payed "+str(amount)+ " and left with "+str(leftPayment)
                })

        else:
            if checkBooking[0].percentagePayed == 100:
                raise ValueError("Already payed the whole sum of payment.")

            minimumAllowedPrice = round(getEvent[0].price * (getEvent[0].minPercentageToPay / 100),2)
            priceLeftToPay = getEvent[0].price - (getEvent[0].price * (checkBooking[0].percentagePayed / 100))

            priceLeftToPay = round(priceLeftToPay,2)

            if amount > priceLeftToPay:
                raise ValueError("The amount that needs to be payed can't be greater than " +str(priceLeftToPay))

            newPricePayed = round(getEvent[0].price * (checkBooking[0].percentagePayed / 100) + amount,2)
            print(newPricePayed)
            #This is where the payment integration will be put    
            newPercentagePayed = round((newPricePayed / getEvent[0].price) * 100,2)
            print(newPercentagePayed)

            checkBooking.update(
                percentagePayed = newPercentagePayed
            )

            leftPayment = round(((100 - newPercentagePayed) / 100 ) * getEvent[0].price,2)

            if newPercentagePayed == 100:
                return Response({
                    "success":True,
                    "message":"Successfully completed the payment for the event."
                })
            return Response({
                    "success":True,
                    "message":"Successfully payed "+str(amount)+ " and left with "+str(leftPayment)
            })
    
    @action(detail=False,methods=['PUT'],url_path='scanQrCodeForGraduationEvents/(?P<key>[A-z0-9]+)')
    def scanQrCodeForGraduationEvents(self,request,format = None, *args, **kwargs):

        organizer = extractToken.checkOrganizerToken(request.headers)

        getEvent = GraduationEvent.objects.filter(eventkey = kwargs['key'])
        if not getEvent.exists():
            raise ValueError("Event not found.")
        
        if 'code' not in request.data.keys():
            raise ValueError("code is a required attribute.")
        
        getBooking = GraduationBooking.objects.filter(code = request.data['code'])

        if not getBooking.exists():
            raise ValueError("no booking with the code entered.")

        if getBooking[0].percentagePayed < 100:
            raise ValueError("Payment not completed.")

        if getBooking[0].has_attended:
            raise ValueError("User has already attended the event.")

        maxNoOfAttendees = getEvent[0].maxNoOfAttendees

        getEvent.update(
            maxNoOfAttendees = maxNoOfAttendees - 1
        )        

        getBooking.update(
            has_attended = True 
        )

        return Response({
            "success":True,
            "message":"Successfully scanned the QR Code.",
            "action":"User can attend the event."
        })
