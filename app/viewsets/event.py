from datetime import datetime
from io import BytesIO


import re,requests,json
from django.utils import timezone
from django.db.models import Count

from rest_framework import status,viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django_filters.rest_framework import DjangoFilterBackend

from urllib.parse import urlparse
from urllib.parse import parse_qs

from app.models import *
from app.serializers import * 
from app.scripts import extractToken,utils,checkOrganizerPlan,notifyAttendees,telebirr,telebirr2,telebirrConnector, firebase_authentication
from app.signals import signals

import qrcode
import qrcode.image.svg
import imghdr
import haversine as hs

import inspect
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP,PKCS1_v1_5
from base64 import b64decode,b64encode 

from django.template.loader import render_to_string 
from django.core.mail import EmailMessage
from django.conf import settings

import cloudinary,cloudinary.uploader,cloudinary.api
class EventViewSet(viewsets.ModelViewSet):

    queryset = Event.objects.filter(isHidden__in = [False])
    serializer_class = EventSerializer
    filter_backends = [filters.SearchFilter,filters.OrderingFilter,DjangoFilterBackend]
    ordering_fields = ['name','normalPrice','vipPrice','vvipPrice','description','startDate','endDate','venue','location','dressingCode','maxNoOfAttendees','noOfViews','isHidden']
    search_fields = ['name','normalPrice','vipPrice','vvipPrice','description','startDate','endDate','venue','location','dressingCode','maxNoOfAttendees','noOfViews','isHidden']
    filter_fields = ['name','normalPrice','vipPrice','vvipPrice','description','startDate','endDate','venue','location','dressingCode','maxNoOfAttendees','noOfViews','isHidden']

    def list(self, request, *args, **kwargs):
        checkEvents = Event.objects.filter(isHidden__in = [False], isPrivate=False)
                
        allEvents = []
        for event in checkEvents:
            singleEvent = {}

            singleEvent['id'] = event.id
            singleEvent['name'] = event.name
            singleEvent['normalPrice'] = event.normalPrice
            singleEvent['vipPrice'] = event.vipPrice
            singleEvent['vvipPrice'] = event.vvipPrice
            singleEvent['description'] = event.description
            singleEvent['startDate'] = event.startDate
            singleEvent['endDate'] = event.endDate
            singleEvent['venue'] = event.venue

            if hasattr(event,'subCategory'):
                singleEvent['subCategory_id'] = event.subCategory.id
                singleEvent['subCategory'] = event.subCategory.title
                singleEvent['category'] = event.subCategory.category.title
                singleEvent['category_id'] = event.subCategory.category.id
            else:
                singleEvent['subCategory_id'] = ""
                singleEvent['subCategory'] = ""
                singleEvent['category'] = ""
                singleEvent['category_id'] = ""
            singleEvent['location'] = event.location
            singleEvent['tags'] = event.tags
            singleEvent['phones'] = event.phones
            singleEvent['image_url'] = event.image_url
            # if hasattr(event,'subCategory'):

            #     singleEvent['createdBy'] = event.createdBy.id
            # else:
            #     singleEvent['createdBy'] = ""

            singleEvent['dressingCode'] = event.dressingCode
            singleEvent['maxNoOfAttendees'] = event.maxNoOfAttendees
            singleEvent['noOfViews'] = event.noOfViews

            allEvents.append(singleEvent)

            # for key in event.keys():
            #     singleEvent[key] = event.key

        return Response(allEvents)

    def create(self,request,format=None):
    
        
        organizer = extractToken.checkOrganizerToken(request.headers)
        organizerSerializer = UserSerialzier(organizer,context={'request': request})

        plan = checkOrganizerPlan.checkOrganizerPlan(organizer)

        #check the required variables are input
        names = ('name','normalPrice','phones','venue','description','startDate','location','tags','maxNoOfAttendees','sub-category')
        if not all(name in request.data.keys() for name in names):
            raise ValueError("All required fields must be input")

        #check the request body is not of string value
        if isinstance(request.data,str):
            raise ValueError("All required fields must be input")
        #check the tags value is a list    
        if not isinstance(request.data['tags'],list):
            raise ValueError("Tags must be an array")
        #check the phones values is a list
        if not isinstance(request.data['phones'],list):
            raise ValueError("Phones must be an array")
        # check the sub-category is of type
        if not isinstance(request.data['sub-category'],int):
            raise ValueError("Sub Category Id must be an integer")

        checkSubCategory = SubCategory.objects.filter(pk = request.data['sub-category'])
        if not checkSubCategory.exists():
            raise ValueError("Sub category does not exist with the id entered")
        
        # subCategorySerializer = SubCategorySerializer(checkSubCategory,many=False,context={'request': request})
        # print(subCategorySerializer.data)
        if not utils.is_datetime(datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M')):
            raise ValueError("Invalid start date format")
        if datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M') < datetime.now():
            raise ValueError("Start Date can not be before the Current time and date")

        if 'endDate' in request.data:
            if not utils.is_datetime(datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M')):
                raise ValueError("Invalid end date format")
            if datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M') < datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M'):
                raise ValueError("End date must be after the start Date")

        # if 'sub-category'
        if not type(request.data['maxNoOfAttendees'] == int):
            raise ValueError("Attendee must be an integer")
        if not request.data['name'] or not request.data['description']:
            raise ValueError("All required fields must be input")
        if not type(request.data['normalPrice']) == int and not type(request.data['normalPrice']) == float:
            raise ValueError("Price must be a number")
        if 'vipPrice' in request.data:
            if not type(request.data['vipPrice']) == int and not type(request.data['vipPrice']) == float:
                raise ValueError("vipPrice must be a number")
            if request.data['vipPrice'] < 0:
                raise ValueError("Price can not be less than 0")
        if 'vvipPrice' in request.data:
            if not type(request.data['vvipPrice']) == int and not type(request.data['vvipPrice']) == float:
                raise ValueError("vvipPrice must be a number")
            if request.data['vvipPrice'] < 0:
                raise ValueError("Price can not be less than 0")
        if 'dressingCode' in request.data:
            if not request.data['dressingCode']:
                raise ValueError("Dressing Code can not be empty")
        if 'venue' in request.data:
            if not request.data['venue']:
                raise ValueError("Venue can not be empty")
        if request.data['normalPrice'] < 0:
            raise ValueError("Price can not be less than 0")
        
        tags = []
        for tag in request.data['tags']:
            if tag[0] != '#':
                tags.append('#' + tag)
            else:
                tags.append(tag)
            # tags.append(TagSerializer(tagObject[0],context={'request':request}).data['url'])
        
        data = {}
        
        data['name'] = request.data['name']
        data['normalPrice'] = request.data['normalPrice']
        data['description'] = request.data['description']
        data['startDate'] = request.data['startDate']
        data['phones'] = request.data['phones']
        data['maxNoOfAttendees'] = request.data['maxNoOfAttendees']
        data['venue'] = request.data['venue']
        # data['subCategory'] = subCategorySerializer.data['url']
        if 'endDate' in request.data:
            data['endDate'] = request.data['endDate']
        if 'vipPrice' in request.data:
            data['vipPrice'] = request.data['vipPrice']
        if 'vvipPrice' in request.data:
            data['vvipPrice'] = request.data['vvipPrice']
        if 'dressingCode' in request.data:
            data['dressingCode'] = request.data['dressingCode']
        data['location'] = request.data['location']
        data['tags'] = tags
        data['createdBy'] = organizer.pk
        
        serializer = EventSerializer(data= data,context={'request': request})
        if not serializer.is_valid():
            return Response({
                "success":False,
                "message":serializer.errors,
                "data":{}
            })
        
        serializer.save()
        
        getCreatedEvent = Event.objects.filter(pk= serializer.data['id'])
        getCreatedEvent.update(
            subCategory = checkSubCategory[0]
        )
        
        signals.notify_followers.send(sender="Event-Creation",event=getCreatedEvent[0],organizer=organizer)
        signals.notify_interested.send(sender="Event-Creation",event=getCreatedEvent[0],organizer=organizer)
        
        return Response({
            "status":True,
            "message":"Successfully Created the Event",
            "data":serializer.data
        })
    
    def retrieve(self, request, *args, **kwargs):
        # return Response({
        #     "success":True
        # })
        attendee = False
        if('Authorization' in request.headers):
            attendee = extractToken.checkAttendeeToken(request.headers)
            
        if attendee:
            signals.add_eventViewers_count.send(sender="user-event",userId=attendee.pk,eventId=kwargs['pk'])
        else:
            print("Hello")
            signals.add_eventViewers_count.send(sender="non-user-event",userId="",eventId=kwargs['pk'])
        return super().retrieve(request, *args, **kwargs) 
    
    def destroy(self,request, *args, **kwargs):

        # pk = kwargs['pk']

        # organizer = extractToken.checkOrganizerToken(request.headers)
        
        # checkEvent = Event.objects.filter(pk = pk)

        # if not checkEvent.exists():
        #     raise ValueError("Event does not exist.")
        
        # if checkEvent[0].createdBy != organizer:
        #     raise ValueError("Not allowed operation")
            
        # checkEvent.delete()

        return Response({
            "success":True,
            "message":"Successfully deleted the event."
        })
    
    def update(self, request, format = None , pk = None):
        organizer = extractToken.checkOrganizerToken(request.headers)
        organizerSerializer = UserSerialzier(organizer,context={'request': request})

        plan = checkOrganizerPlan.checkOrganizerPlan(organizer)

        # checks the event
        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event not found")
        
        # checks if the event has been created by the organizer
        if organizer.pk != checkEvent[0].createdBy.pk:
            raise ValueError("Action not allowed")

        # checks if the event has not been started
        if checkEvent[0].startDate < timezone.now():
            raise ValueError("Cant edit started events.")

        data = {}
        
        data['name'] = checkEvent[0].name
        data['normalPrice'] = checkEvent[0].normalPrice
        data['description'] = checkEvent[0].description
        data['startDate'] = checkEvent[0].startDate
        data['phones'] = checkEvent[0].phones
        data['maxNoOfAttendees'] = checkEvent[0].maxNoOfAttendees
        data['venue'] = checkEvent[0].venue
        # data['subCategory'] = subCategorySerializer.data['url']
        data['endDate'] = checkEvent[0].endDate
        data['vipPrice'] = checkEvent[0].vipPrice
        data['vvipPrice'] = checkEvent[0].vvipPrice
        data['dressingCode'] = checkEvent[0].dressingCode
        data['location'] = checkEvent[0].location
        data['tags'] = checkEvent[0].tags

        #check the required variables are input
        names = ('name','normalPrice','phones','venue','description','startDate','location','tags','maxNoOfAttendees','sub-category')
        if not all(name in request.data.keys() for name in names):
            raise ValueError("All required fields must be input")

        #check the request body is not of string value
        if isinstance(request.data,str):
            raise ValueError("All required fields must be input")
        #check the tags value is a list    
        if not isinstance(request.data['tags'],list):
            raise ValueError("Tags must be an array")
        #check the phones values is a list
        if not isinstance(request.data['phones'],list):
            raise ValueError("Phones must be an array")
        # check the sub-category is of type
        if not isinstance(request.data['sub-category'],int):
            raise ValueError("Sub Category Id must be an integer")
        
        checkSubCategory = SubCategory.objects.filter(pk = request.data['sub-category'])
        if not checkSubCategory.exists():
            raise ValueError("Sub category does not exist with the id entered")
        if not utils.is_datetime(datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M')):
            raise ValueError("Invalid start date format")
        if datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M') < datetime.now():
            raise ValueError("Start Date can not be before the Current time and date")

        if 'endDate' in request.data:
            if not utils.is_datetime(datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M')):
                raise ValueError("Invalid end date format")
            if datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M') < datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M'):
                raise ValueError("End date must be after the start Date")
        
        if not type(request.data['maxNoOfAttendees'] == int):
            raise ValueError("Attendee must be an integer")
        if not request.data['name'] or not request.data['description']:
            raise ValueError("All required fields must be input")
        if not type(request.data['normalPrice']) == int and not type(request.data['normalPrice']) == float:
            raise ValueError("Price must be a number")
        if 'vipPrice' in request.data:
            if not type(request.data['vipPrice']) == int and not type(request.data['vipPrice']) == float:
                raise ValueError("vipPrice must be a number")
            if request.data['vipPrice'] < 0:
                raise ValueError("Price can not be less than 0")
        if 'vvipPrice' in request.data:
            if not type(request.data['vvipPrice']) == int and not type(request.data['vvipPrice']) == float:
                raise ValueError("vvipPrice must be a number")
            if request.data['vvipPrice'] < 0:
                raise ValueError("Price can not be less than 0")
        if 'dressingCode' in request.data:
            if not request.data['dressingCode']:
                raise ValueError("Dressing Code can not be empty")
        if 'venue' in request.data:
            if not request.data['venue']:
                raise ValueError("Venue can not be empty")
        if request.data['normalPrice'] < 0:
            raise ValueError("Price can not be less than 0")
        
        tags = []
        for tag in request.data['tags']:
            if tag[0] != '#':
                tags.append('#' + tag)
            else:
                tags.append(tag)
        
        data['name'] = request.data['name']
        data['normalPrice'] = request.data['normalPrice']
        data['description'] = request.data['description']
        data['startDate'] = request.data['startDate']
        data['phones'] = request.data['phones']
        data['maxNoOfAttendees'] = request.data['maxNoOfAttendees']
        data['venue'] = request.data['venue']
        # data['subCategory'] = subCategorySerializer.data['url']
        if 'endDate' in request.data:
            data['endDate'] = request.data['endDate']
        if 'vipPrice' in request.data:
            data['vipPrice'] = request.data['vipPrice']
        if 'vvipPrice' in request.data:
            data['vvipPrice'] = request.data['vvipPrice']
        if 'dressingCode' in request.data:
            data['dressingCode'] = request.data['dressingCode']
        data['location'] = request.data['location']
        data['tags'] = tags
        
        print(data['vvipPrice'])
        checkEvent.update(
            name = data['name'],
            normalPrice = data['normalPrice'],
            description = data['description'],
            startDate = data['startDate'],
            phones = data['phones'],
            maxNoOfAttendees = data['maxNoOfAttendees'],
            venue = data['venue'],
            endDate = data['endDate'],
            vipPrice = data['vipPrice'],
            vvipPrice = data['vvipPrice'],
            dressingCode = data['dressingCode'],
            location = data['location'],
            tags = data['tags'],
            subCategory = checkSubCategory[0],
        )

        return Response({
            "status":True,
            "message":"event has been successfully edited",
            "data":utils.eventFormatter(checkEvent)
        })

    # search events by name
    @action(detail = False, methods=['GET'],url_path='searchEvent/name/(?P<event_name>[A-z0-9]+)')
    def searchEvent(self,request, format = None,*args,**kwargs):
        name = kwargs['event_name']

        checkEvent = Event.objects.filter(name__icontains = name,isHidden__in = [False])
        
        if not checkEvent.exists():
            raise ValueError("Event not found.")

        return Response({
            "success":True,
            "data":utils.eventFormatter(checkEvent)
        })
        
    # method to check telebirr mobile money app payment
    @action(detail = False,methods=['PUT'])
    def telebirrPayment(self,request, format = None):
        
        telebirrObj = telebirr2.Telebirr(1,"20Wifi Bill")
        checkoutUrl = telebirrObj.send_request()
        # print(telebirr.getRequestData())

        # url = 'http://196.188.120.3:11443/service-openup/toTradeWebPay'
        # response = requests.post(url = url,json = telebirr.getRequestData())
        # print(response.text)  
        url = checkoutUrl['data']['toPayUrl']
        parsedUrl = urlparse(url, allow_fragments=False)
        transactionNo = parse_qs(parsedUrl.query)['transactionNo'][0]

        print(transactionNo)
        return Response({
            "success":True,
            "message":"To complete the payment please redirect to the url.",
            "data":checkoutUrl
        })

    # method to be notified of telebirr payment success
    @action(detail = False, methods = ['POST'])
    def telebirrNotify(self, request, format = None):

        # print(self.methods)
        # print(request.query_params)
        # print(request.headers)
        # print(dir(request))
        # print(request.data)
        # print(request.data)

        public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAjmOH9PP85S7gAS+zBJKQCDfJdUGkrBkKyECTJcRq/FqEiKb3DlmwZs0FX6TaEqgyqLcKFFFcjVm1pXi5qVOKg269atQJHiDeNQZbJjHt1ySmx8yp2l6z9yAm4agB75mfjgge17ND2WlqblIgKIrGmAKWKWhMOdwdT4eFMXYYdTJ1RLThAisSsSNyNFtiSxU5mXTx/WH//tvoy9CiSTd/tMUwF6JNmqyebdqA5mVwbjHC9916+STCTzyW1d6IfYQZz/SbCyu7qUD+xFRqQgDhZbA/DTY7Jbw+QLt216UhU1GoUQyRpi1v3qHLkMkos9NOVBxHtv+a47eTxXQYluQZCQIDAQAB"
        public_key = re.sub("(.{64})", "\\1\n", public_key.replace("\n", ""), 0, re.DOTALL)
        public_key = '-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----'.format(public_key)

        rsa_private_key = RSA.importKey(public_key)
        # encrypt_byte = b64decode(request.data['data'].encode())
        # length = len(encrypt_byte)
        msg = request.data['data']
        cipher = PKCS1_v1_5.new(rsa_private_key)
        ciphertext = b''
        for i in range(0,len(msg) //117):
            ciphertext += cipher.encrypt(msg[i * 117:(i + 1) * 117].encode('utf8'))
        ciphertext += cipher.decrypt(msg[(len(msg) // 117) * 117:len(msg)].encode('utf8'),'failure')
        print(ciphertext)
        # print(cipher.decrypt(encrypt_byte, 'failure'))
        # if length < 128:
        #     dec
        # rsa_private_key = PKCS1_OAEP.new(rsa_private_key)
        # decrypted_text = rsa_private_key.decrypt(request.data['data'])

        # print(decrypted_text)


        return Response({
            "success":True
        })

    # method to be seen as telebirr success
    @action(detail = False,methods = ['GET'])
    def telebirrSuccess(self, request, format = None):
        return Response({
            "success":True
        })

    # method to upload images for events
    @action(detail= True,methods=['PUT'])
    def uploadEventImage(self,request,pk = None,format = None):
        # checks the event and organizer from the request parameter and header
        organizer = extractToken.checkOrganizerToken(request.headers)
        
        checkEvent = Event.objects.filter(pk = pk)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        # checks if the organizer is the creater of the event
        if organizer.pk != checkEvent[0].createdBy.pk:
                raise ValueError("Action not allowed")

        # defines the allowed types for the event and 
        # checks the input image is in the in the allowed list of image types
        allowedTypes = ['png','jpg','jpeg']
        # checks if the image is present in the request files 
        if not 'image' in request.FILES.keys():
            raise ValueError("Image must be provided")

        image = request.FILES['image']
        if imghdr.what(image) not in allowedTypes:
            raise ValueError("Image must of png,jpg or jpeg types")
        
        # uploads the image to cloudinary with the appropriate data
        uploadedFile = cloudinary.uploader.upload(
            image,
            folder = "MinAleAddis/Events/Images/",
            public_id = "Event " + str(pk) + " image",
            overwrite = True,
            resource_type = "image" 
        )

        # saves the image url on the event object
        checkEvent.update(
            image_url = uploadedFile['url']
        )
        
        return Response({
            "success":True,
            "message":"Successfully uploaded the image for the event " + str(checkEvent[0].name)
        })

    # assign Usher to Event 
    @action(detail = True,methods=['PUT'])
    def assignUsher(self, request,pk = None,format = None):
        # checks the event and organizer from the request parameter and header
        organizer = extractToken.checkAdminOrOrganizer(request.headers)

        if 'name' not in request.data.keys():
            raise ValueError("Name is a required attribute")

        checkEvent = Event.objects.filter(pk = pk)

        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Cant assign ushers to ended events")

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        # checks if the organizer is the creater of the event
        if organizer.pk != checkEvent[0].createdBy.pk:
                raise ValueError("Action not allowed")
        
        createdUsher = Usher.objects.create(
            name = request.data['name'],
            code = utils.randomNumberGenerator(6),
            event = checkEvent[0]
        )


        return Response({
            "success":True,
            "message":"Successfully added the usher for the event",
            "data":{
                "code":createdUsher.code
            } 
        })
    
    @action(detail= True,methods=['GET'])
    def getAllAssignedUshers(self,request ,pk = None, format = None):

        # checks the event and organizer from the request parameter and header
        organizer = extractToken.checkAdminOrOrganizer(request.headers)

        checkEvent = Event.objects.filter(pk = pk)

        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Event has already ended.")

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        # checks if the organizer is the creater of the event
        if organizer.pk != checkEvent[0].createdBy.pk:
                raise ValueError("Action not allowed")
        
        getUshers = Usher.objects.filter(event = checkEvent[0])
        
        allUshers = []
        for usher in getUshers:
            singleUsher = {}
            singleUsher['name'] = usher.name
            singleUsher['code'] = usher.code

            allUshers.append(singleUsher)

        return Response({
            "success":True,
            "data":allUshers
        })

    @action(detail= False,methods=['GET'])
    def getVirtualEvents(self,request,format = None):

        virtualEvents = Event.objects.filter(isVirtual__in = [True],startDate__gte = timezone.now())
        
        return Response({
            "success":True,
            "data":utils.eventFormatter(virtualEvents)
        })

    @action(detail = False,methods=['POST'])
    def createVirtualEvent(self,request,format = None):
        
        organizer = extractToken.checkOrganizerToken(request.headers)
        organizerSerializer = UserSerialzier(organizer,context={'request': request})

        names = ('name','normalPrice','phones','venue','description','startDate','tags','maxNoOfAttendees','sub-category')
        if not all(name in request.data.keys() for name in names):
            raise ValueError("All required fields must be input")
        
        #check the request body is not of string value
        if isinstance(request.data,str):
            raise ValueError("All required fields must be input")
        #check the tags value is a list    
        if not isinstance(request.data['tags'],list):
            raise ValueError("Tags must be an array")
        #check the phones values is a list
        if not isinstance(request.data['phones'],list):
            raise ValueError("Phones must be an array")
        # check the sub-category is of type
        if not isinstance(request.data['sub-category'],int):
            raise ValueError("Sub Category Id must be an integer")
        
        checkSubCategory = SubCategory.objects.filter(pk = request.data['sub-category'])
        if not checkSubCategory.exists():
            raise ValueError("Sub category does not exist with the id entered")
        
        if not utils.is_datetime(datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M')):
            raise ValueError("Invalid start date format")
        if datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M') < datetime.now():
            raise ValueError("Start Date can not be before the Current time and date")

        if 'endDate' in request.data:
            if not utils.is_datetime(datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M')):
                raise ValueError("Invalid end date format")
            if datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M') < datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M'):
                raise ValueError("End date must be after the start Date")

        # if 'sub-category'
        if not type(request.data['maxNoOfAttendees'] == int):
            raise ValueError("Attendee must be an integer")
        if not request.data['name'] or not request.data['description']:
            raise ValueError("All required fields must be input")
        
        if not type(request.data['normalPrice']) == int and not type(request.data['normalPrice']) == float:
            raise ValueError("Price must be a number")
        if 'venue' in request.data:
            if not request.data['venue']:
                raise ValueError("Venue can not be empty")
        if request.data['normalPrice'] < 0:
            raise ValueError("Price can not be less than 0")
        
        tags = []
        for tag in request.data['tags']:
            if tag[0] != '#':
                tags.append('#' + tag)
            else:
                tags.append(tag)
        
        data = {}
        
        data['name'] = request.data['name']
        data['normalPrice'] = request.data['normalPrice']
        data['description'] = request.data['description']
        data['startDate'] = request.data['startDate']
        data['phones'] = request.data['phones']
        data['maxNoOfAttendees'] = request.data['maxNoOfAttendees']
        data['venue'] = request.data['venue']
        # data['subCategory'] = subCategorySerializer.data['url']
        if 'endDate' in request.data:
            data['endDate'] = request.data['endDate']
        data['location'] = "0.00000000,0.00000000"
        data['isVirtual'] = True
        data['tags'] = tags
        data['createdBy'] = organizer.pk

        serializer = EventSerializer(data= data,context={'request': request})
        if not serializer.is_valid():
            return Response({
                "success":False,
                "message":serializer.errors,
                "data":{}
            })
        
        serializer.save()
        
        getCreatedEvent = Event.objects.filter(pk= serializer.data['id'])
        getCreatedEvent.update(
            subCategory = checkSubCategory[0],
            isVirtual = True
        )
        signals.notify_followers.send(sender="Event-Creation",event=getCreatedEvent[0],organizer=organizer)
        return Response({
            "status":True,
            "message":"Successfully Created the Virtual Event",
            "data":serializer.data
        })
        

    
    @action(detail=False,methods=['GET'],url_path='getEventByTag/(?P<tag>[A-z0-9]+)')
    def getEventByTag(self,request,format=None,*args, **kwargs):
        
        checkEvents = Event.objects.filter(tags__contains= kwargs['tag'],isHidden__in = [False])

        if not checkEvents.exists():
            return Response({
                "success":False,
                "message":"No events by the tag input",
                "data":[]
            })

        return Response({
            "success":True,
            "message":"Event/s found for the input tag",
            "data":utils.eventFormatter(checkEvents)
        })

    @action(detail=True,methods=['GET'])
    def getEventSales(self,request,pk=None,format=None):
        
        user = extractToken.checkAdminOrOrganizer(request.headers)

        checkEvent = Event.objects.filter(pk = pk ,isHidden__in = [False])
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        if user.isOrganizer == True:
            if user.pk != checkEvent[0].createdBy.pk:
                raise ValueError("Action not allowed")

        checkBookings = Booking.objects.filter(event = checkEvent[0])
        
        if not checkBookings.exists():
            return Response(
                {
                    "Success":False,
                    "message":"No sales or bookings for the event",
                    "data":[]
                }
            )

        confirmedSales = []
        unconfirmedBookings = []

        for booking in checkBookings:
            singleBooking = {}

            singleBooking['userId'] = booking.attendee.pk
            singleBooking['username'] = booking.attendee.username
            singleBooking['fullname'] = booking.attendee.first_name + " " + booking.attendee.last_name
            singleBooking['type'] =  booking.type
            singleBooking['timestamp'] = booking.timestamp
            singleBooking['number'] = booking.number
                
            if booking.has_attended == True:
                confirmedSales.append(singleBooking)
            
            else:
                unconfirmedBookings.append(singleBooking)

        return Response({
            "Success":True,
            "message":"Found event sales and bookings",
            "data":{
                "confirmedSales":confirmedSales,
                "unconfirmedBookings":unconfirmedBookings
            }
        })

    @action(detail=False,methods=['GET'])
    def getEventByMostSeen(self,request,format = None):
        most_seen = Event.objects.filter(isHidden__in = [False]).exclude(noOfViews  = 0,).order_by('-noOfViews')

        if not most_seen.exists():
            return Response({
                "success":False,
                "data":[]
            })
        if len(most_seen) >= 5:
            most_seen = utils.eventFormatter(most_seen[0:5]) 
        # print(most_seen[len(most_seen) -1].noOfViews)
        else:
            most_seen = utils.eventFormatter(most_seen)
        return Response(
            {
                "success":True,
                "data":most_seen
            })

    @action(detail=False,methods=['GET'])
    def getMostBoughtEvents(self,request,format=None):
        booking = Booking.objects.filter(has_attended = True).annotate(mb = Count('event')).order_by('-mb')

        if not booking:
            return Response({
                "success":False,
                "data":[]
            })

        mostBooked = Event.objects.filter(booking__in = booking)
        

        if len(mostBooked) >= 5:
            mostBooked = utils.eventFormatter(mostBooked[0:5])
        else:
            mostBooked = utils.eventFormatter(mostBooked)
        
        return Response({
            "success":True,
            "data":mostBooked
        })
    
    @action(detail=False,methods=['GET'])
    def getMostRatedEvents(self,request,format=None):
        
        ratings = Review.objects.filter().annotate(mr = Count('event')).order_by('-mr')

        if not ratings:
            return Response({ 
                "success":False,
                "data":[]
            })

        mostRated = Event.objects.filter(review__in = ratings)

        if len(mostRated) >= 5:
            mostRated = utils.eventFormatter(mostRated[0:5])
        else:
            mostRated = utils.eventFormatter(mostRated)
        
        return Response({
            "success":True,
            "data":mostRated
        })

    @action(detail=False,methods=['GET'],url_path=r'(?P<event_id>\d+)/getEventLikes')
    def getEventLikes(self,request,format=None,*args, **kwargs):
        
        eventId = kwargs['event_id']
        checkEvent = Event.objects.filter(pk = eventId)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        likedBy = checkEvent[0].likedBy.all()
        if not likedBy:
            return Response({
                "success":"True",
                "message":"Event not liked by any attendee",
                "data":[]
            })

        usersLiked = []
        for user in likedBy:
            userLiked = {}
            userLiked['username'] = user.username
            userLiked['first_name'] = user.first_name
            userLiked['last_name'] = user.last_name
            userLiked['id'] = user.pk
            usersLiked.append(userLiked)
        
        return Response({
            "success":True,
            "message":"Found users who liked the event",
            "data":{
                "users":usersLiked,
                "count":len(usersLiked)
                }
        })

    # endpoint for organizers to see who has viewed the specific event
    @action(detail=False,methods=['GET'],url_path=r'(?P<event_id>\d+)/getEventViewers')
    def getEventViewers(self,request,format=None,*args, **kwargs):


        organizer = extractToken.checkOrganizerToken(request.headers)

        eventId = kwargs['event_id']
        checkEvent = Event.objects.filter(pk = eventId)

        if not checkEvent[0].createdBy == organizer :
            raise ValueError("Event not created by organizer")
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        viewers = EventSeen.objects.filter(event = checkEvent[0])

        if len(viewers) == 0:
            return Response({
                "success":False,
                "message":"No registered users have viewed the event",
                "registeredViewers":[],
                "unregisteredViewers":checkEvent[0].noOfViews
            })

        usersViewed = []
        for viewer in viewers:
            userViewed = {}
            userViewed['username'] = viewer.attendee.username
            userViewed['first_name'] = viewer.attendee.first_name
            userViewed['last_name'] = viewer.attendee.last_name
            userViewed['id'] = viewer.pk

            usersViewed.append(userViewed)



        return Response({
            "success":True,
            "message":str(len(viewers)) + " registered user/s viewed the event",
            "registeredViewers":usersViewed,
            "unregisteredViewers":checkEvent[0].noOfViews - len(viewers)
        })

    # endpoint to add to featured events
    @action(detail = True,methods=['POST'] )
    def addToFeaturedEvents(self, request, format = None, pk = None):
        
        admin = extractToken.checkAdminToken(request.headers)

        checkEvent = Event.objects.filter(pk=pk)
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        checkFeaturedEvent = FeaturedEvent.objects.filter(event = checkEvent[0])

        if checkFeaturedEvent.exists():
            raise ValueError("Event is already featured")

        FeaturedEvent.objects.create(
            event = checkEvent[0]
        )

        return Response({
            "success":True,
            "message":"Successfully added the event to featured events."
        })
    
    # endpoint to remove event from featured events
    @action(detail = True,methods=['PUT'] )
    def removeFromFeaturedEvents(self, request, format = None, pk = None):

        admin = extractToken.checkAdminToken(request.headers)

        checkEvent = Event.objects.filter(pk=pk)
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkFeaturedEvent = FeaturedEvent.objects.filter(event = checkEvent[0])

        if not checkFeaturedEvent.exists():
            raise ValueError("Event is not featured")

        checkFeaturedEvent.delete()

        return Response({
            "success":True,
            "message":"Succesfully removed event from featured events."
        })


    # endpoint to reserve events
    @action(detail=True,methods=['POST'])
    def reserveEvent(self,request,pk=None,format=None):

        attendee = extractToken.checkAttendeeToken(request.headers)

        if attendee.profile_completed == False:
            raise ValueError("Profile must be completed.")

        checkEvent = Event.objects.filter(pk=pk)
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        if checkEvent[0].normalPrice != 0 or checkEvent[0].vipPrice or checkEvent[0].vvipPrice:
            raise ValueError("Only free events are allowed")
        
        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Event has already ended")

        if not 'number' in request.data:
            raise ValueError("All required fields must be input")
        
        if not isinstance(request.data['number'],int):
            raise ValueError("Invalid number")
        
        if request.data['number'] < 1 or request.data['number'] > 10:
            raise ValueError("Reservations should be between 1 and 10")
        
        if request.data['number'] > checkEvent[0].maxNoOfAttendees:
            raise ValueError("No reservation spots left for this number.")
        checkReservation = Reservation.objects.filter(attendee = attendee,event = checkEvent[0])

        if checkReservation.exists():
            raise ValueError("User already reserved for this event")

        checkEvent.update(
            maxNoOfAttendees = checkEvent[0].maxNoOfAttendees - int(request.data['number'])
        )

        # if not (4 + timezone.now().day) < (checkEvent[0].startDate.day):
        #     raise ValueError("Can only reserve events before 4 days of the starting date") 
        
        createdReservation = Reservation.objects.create(
            attendee = attendee,
            event = checkEvent[0],
            number = request.data['number']
        )

        return Response({
            "status":True,
            "message":"Succesfully made the reservation",
            "data":{
                "reservation_id":createdReservation.pk,
                "space_left":createdReservation.event.maxNoOfAttendees
            }
        })
    
    @action(detail=True,methods=['POST'])
    def cancelReservation(self,request,pk=None,format=None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        checkEvent = Event.objects.filter(pk=pk)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkReservation = Reservation.objects.filter(attendee = attendee,event = checkEvent[0])
        if not checkReservation.exists():
            raise ValueError("Attendee has not reserved this event")
        
        checkReservation.delete()
        checkEvent.update(
            maxNoOfAttendees = checkEvent[0].maxNoOfAttendees + 1
        )

        return Response({
            "status":True,
            "message":"Successfully canceled the reservation for the event " + str(checkEvent[0].name)
        })

    @action(detail=True,methods=['POST'])
    def bookByPromoEvent(self,request,pk = None,format = None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        if attendee.profile_completed == False:
            raise ValueError("Profile must be completed.")

        checkEvent = Event.objects.filter(pk=pk)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        if not 'type' or not 'number' or not 'code' in request.data:
            raise ValueError("All required fields must be input")
        
        if not request.data['type'] in ['N','V','VV']:
            raise ValueError("Type not allowed")

        if not isinstance(request.data['number'],int):
            raise ValueError("Invalid number")
        
        if request.data['number'] < 1 or request.data['number'] > 10:
            raise ValueError("Bookings should be between 1 and 10")
        
        if request.data['type'] == 'V':
            if checkEvent[0].vipPrice == 0:
                raise ValueError("Vip does not exist for event")
        elif request.data['type'] == 'VV':
            if checkEvent[0].vvipPrice == 0:
                raise ValueError("VVip does not exist for event")

        else:
            if checkEvent[0].normalPrice == 0 and request.data['number'] != 0:
                raise ValueError("Event is free ")
            
        checkPromoCode = PromoCode.objects.filter(event = checkEvent[0], code = request.data['code'])
        if not checkPromoCode.exists():
            raise ValueError("Promo Code does not exist")
        
        if request.data['type'] == 'V':
            print(checkEvent[0].vipPrice * request.data['number'])
            print(checkEvent[0].vipPrice * request.data['number'] - checkEvent[0].vipPrice * request.data['number'] * (checkPromoCode[0].percentage_decrease/100))

        elif request.data['type'] == 'VV':
            print(checkEvent[0].vvipPrice * request.data['number'])
            print(checkEvent[0].vvipPrice * request.data['number'] - checkEvent[0].vvipPrice * request.data['number'] * (checkPromoCode[0].percentage_decrease/100))

        else:
            print(checkEvent[0].normalPrice * request.data['number'])
            print(checkEvent[0].normalPrice * request.data['number'] - checkEvent[0].normalPrice * request.data['number'] * (checkPromoCode[0].percentage_decrease/100))

        checkBooking = Booking.objects.filter(attendee = attendee,event = checkEvent[0])
        if checkBooking.exists():
            raise ValueError("User already booked for this event")
            
        code = utils.randomCodeGenerator(10)

        context = {}
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(code,image_factory=factory,box_size=40)
        
        stream = BytesIO()
        img.save(stream)

        #This is the part where the payment Integration will be made
        #
        uploadedfile = cloudinary.uploader.upload(
            stream.getvalue(), 
            folder = "MinAleAddis/QRCodes/", 
            public_id = code+'qrcode',
            overwrite = True,  
            resource_type = "image"
        )

        Booking.objects.create(
            attendee = attendee,
            event = checkEvent[0],
            type = request.data['type'],
            number = request.data['number'],
            code = code,
            qrcode = uploadedfile['url']
        )

        
        return Response({
            "success":True,
            "message":"Successfully booked for event " + str(checkEvent[0].name)
        })
    @action(detail=True,methods=['POST'])
    def bookEventFromWallet(self,request,pk=None,format=None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        if attendee.profile_completed == False:
            raise ValueError("Profile must be completed.")

        checkEvent = Event.objects.filter(pk=pk)
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        if not 'type' or not 'number' in request.data:
            raise ValueError("All required fields must be input")
        
        if not request.data['type'] in ['N','V','VV']:
            raise ValueError("Type not allowed")
        
        if not isinstance(request.data['number'],int):
            raise ValueError("Invalid number")
        
        if request.data['type'] == 'V':
            if checkEvent[0].vipPrice == 0:
                raise ValueError("Vip does not exist for event")
        elif request.data['type'] == 'VV':
            if checkEvent[0].vvipPrice == 0:
                raise ValueError("VVip does not exist for event")

        else:
            if checkEvent[0].normalPrice == 0 and request.data['number'] != 0:
                raise ValueError("Event is free ")
        
        checkBooking = Booking.objects.filter(attendee = attendee,event = checkEvent[0])
        if checkBooking.exists():
            raise ValueError("User already booked for this event")

        checkWallet = Wallet.objects.filter(attendee = attendee)
        checkWalletConfig = WalletConfig.objects.filter()

        if not checkWallet.exists():
            raise ValueError("You don't have sufficient coins to book this event.")
        
        if not checkWalletConfig.exists():
            raise ValueError("Wallet config not found,please contact the adminstrator.")

        chosenPrice = 0
        if request.data['type'] == 'V':
            chosenPrice = checkEvent[0].vipPrice * request.data['number']

        elif request.data['type'] == 'VV':
            chosenPrice = checkEvent[0].vvipPrice * request.data['number']

        else:
            chosenPrice = checkEvent[0].normalPrice * request.data['number']
        
        myCoin = checkWallet[0].coin
        print(chosenPrice)
        print(checkWallet[0].coin * checkWalletConfig[0].coinToBirr )

        if  chosenPrice > checkWallet[0].coin * checkWalletConfig[0].coinToBirr:
            raise ValueError("You don't have sufficient coins to book this event.")\

        else:

            code = utils.randomCodeGenerator(10)

            context = {}
            factory = qrcode.image.svg.SvgImage
            img = qrcode.make(code,image_factory=factory,box_size=40)
            
            stream = BytesIO()
            img.save(stream)

            #This is the part where the payment Integration will be made
            #
            uploadedfile = cloudinary.uploader.upload(
                stream.getvalue(), 
                folder = "MinAleAddis/QRCodes/", 
                public_id = code+'qrcode',
                overwrite = True,  
                resource_type = "image"
            )

            Booking.objects.create(
                attendee = attendee,
                event = checkEvent[0],
                type = request.data['type'],
                number = request.data['number'],
                code = code,
                qrcode = uploadedfile['url']
            )

            checkWallet.update(
                coin = myCoin - (chosenPrice / checkWalletConfig[0].coinToBirr )
            )

            
            return Response({
                "success":True,
                "message":"Successfully booked for event " + str(checkEvent[0].name)
            })
        

    @action(detail=True,methods=['POST'])
    def bookEvent(self,request,pk=None,format=None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)
        if attendee.profile_completed == False:
            raise ValueError("Profile must be completed.")

        checkEvent = Event.objects.filter(pk=pk)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Event has already ended")

        if not 'type' or not 'number' in request.data:
            raise ValueError("All required fields must be input")
        
        if not request.data['type'] in ['N','V','VV']:
            raise ValueError("Type not allowed")

        if not isinstance(request.data['number'],int):
            raise ValueError("Invalid number")
        
        if request.data['number'] < 1 or request.data['number'] > 10:
            raise ValueError("Bookings should be between 1 and 10")
        
        totalPrice = 0
        if request.data['type'] == 'V':
            if checkEvent[0].vipPrice == 0:
                raise ValueError("Vip does not exist for event")
            totalPrice = checkEvent[0].vipPrice * request.data['number']
        elif request.data['type'] == 'VV':
            if checkEvent[0].vvipPrice == 0:
                raise ValueError("VVip does not exist for event")
            totalPrice = checkEvent[0].vvipPrice * request.data['number']
        else:
            if checkEvent[0].normalPrice == 0 and request.data['number'] != 0:
                raise ValueError("Event is free ")
            totalPrice = checkEvent[0].normalPrice * request.data['number']
        
        checkBooking = Booking.objects.filter(attendee = attendee,event = checkEvent[0])
        if checkBooking.exists():
            if checkBooking[0].is_verified == True:
                raise ValueError("User already booked for this event")
            else:
                checkBookingPayment = BookingPayment.objects.filter(booking = checkBooking[0])
                if checkBookingPayment.exists():
                    checkBookingPayment.delete()
                checkBooking.delete()
                

        code = utils.randomCodeGenerator(10)
        item = "User "+str(attendee.pk) +" booking event "+str(checkEvent[0].pk)
        checkoutUrl,transactionNo = telebirrConnector.bookWithTelebirr(totalPrice,item)

        context = {}
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(code,image_factory=factory,box_size=40)
        
        stream = BytesIO()
        img.save(stream)

        
        uploadedfile = cloudinary.uploader.upload(
            stream.getvalue(), 
            folder = "MinAleAddis/QRCodes/", 
            public_id = code+'qrcode',
            overwrite = True,  
            resource_type = "image"
        )

        createdBooking = Booking.objects.create(
            attendee = attendee,
            event = checkEvent[0],
            type = request.data['type'],
            number = request.data['number'],
            code = code,
            qrcode = uploadedfile['url'],
            is_verified = False
        )

        createdBookingPayment = BookingPayment.objects.create(
            transactionNo = transactionNo,
            booking = createdBooking,
            amount = totalPrice
        )

        
        return Response({
            "success":True,
            "message":"Confirm the booking with the Url sent.",
            "data":{
                "checkout_url":checkoutUrl['data']['toPayUrl'],
                "booking_id":createdBooking.pk,
                "amount":totalPrice
            }
        })
    
    @action(detail=True,methods=['PUT'])
    def scanEventCode(self,request,pk=None,format=None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk=pk)

        if not 'code' in request.data.keys():
            raise ValueError("All required values must be input")
        if not checkEvent.exists():
            return ValueError("Event does not exist")
        
        checkBooking = Booking.objects.filter(code=request.data['code'])
        if not checkBooking.exists():
            return ValueError("Booking does not exist")
        
        if checkBooking[0].is_verified == False:
            raise ValueError("User has not completed payment for the booking.")

        if checkBooking[0].has_attended == True:
            return Response({
            "Success":False,
            "message":"Succesfully Scanned the QR Code",
            "action":"User has already attended the event"
            })

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
    
    @action(detail=True,methods=['GET'])
    def getListOfAttendees(self,request,pk=None,format=None):

        user = extractToken.checkAdminOrOrganizer(request.headers)

        
        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        if user.isOrganizer == True:
            if checkEvent[0].createdBy != user:
                raise ValueError("Event not allowed for organizer")

        reservations = Reservation.objects.filter(event = checkEvent[0])
        bookings = Booking.objects.filter(event = checkEvent[0])

        allReservations = []
        allBookings = []

        for booking in bookings:
            singleBooking = {}
            singleBooking['user'] = {
               'username': booking.attendee.username,
               'id': booking.attendee.pk,
               'first_name': booking.attendee.first_name,
               'last_name': booking.attendee.last_name
            }
            singleBooking['time'] = booking.timestamp
            singleBooking['type'] = booking.type
            singleBooking['number'] = booking.number
            singleBooking['has_attended'] = booking.has_attended
            
            allBookings.append(singleBooking)
        
        for reservation in reservations:
            singleReservation = {}
            singleReservation['user'] = {
               'username': reservation.attendee.username,
               'id': reservation.attendee.pk,
               'first_name': reservation.attendee.first_name,
               'last_name': reservation.attendee.last_name
            }
            singleReservation['time'] = reservation.timestamp
            singleReservation['number'] = reservation.number 
            singleReservation['pending_status'] = reservation.pending_status

            allReservations.append(singleReservation)

        return Response({
            "Success":True,
            "bookings":allBookings,
            "reservations":allReservations
        })
    
    @action(detail=False,methods=['POST'])
    def getNearbyCompetitions(self,request,format=None,*args, **kwargs):
        # ,url_path=r'getNearbyCompetitions/long=(?P<longitude>\d\.\d{13})&lat=(?P<latitude>\d\.\d{13})'
        attendee = extractToken.checkAttendeeToken(request.headers)

        #get user's location from request path
        latitude = request.data['Latitude']
        longitude = request.data['Longitude']
        
        if(not isinstance(latitude, float) or not isinstance(longitude, float)): raise ValueError("The values must be in correct longitude and latitude format")
        if(not -180 <= longitude <= 180 or not -90 <= latitude <= 90): raise ValueError("The values must be in correct longitude and latitude format")

        events = Event.objects.filter(endDate__gt= timezone.now(),isHidden__in = [False])
        
        nearbyEvents = []
        for event in events:

            index = event.location.find(',')

            lat = event.location[:index]
            long = event.location[index+1:]

            loc1 = (latitude,longitude)
            loc2 = (float(lat),float(long))

            distance = hs.haversine(loc1,loc2)
            
            if ( distance < 11):
                nearbyEvent = {}

                nearbyEvent['name'] = event.name
                nearbyEvent['id'] = event.pk
                nearbyEvent['distance'] = str(distance) + " kms"

                nearbyEvents.append(nearbyEvent)
        if nearbyEvents != None:
            return Response({
                "Success":True,
                "message":"Found nearby events",
                "data":nearbyEvents
            })
        else :
            return Response({
                "Success":False,
                "message":"Found no nearby events",
                "data":[]
            })

    @action(detail=True,methods=['POST'])
    def createReview(self,request,pk,format = None):
        attendee = extractToken.checkAttendeeToken(request.headers)
        
        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        checkReview = Review.objects.filter(event = checkEvent[0],attendee = attendee)
        if checkReview.exists():
            raise ValueError("Attendee already reviewed the event")

        checkBooking = Booking.objects.filter(event = checkEvent[0],attendee = attendee)

        if not checkBooking.exists():
            raise ValueError("User must attend the event before reviewing")

        if checkBooking[0].has_attended != True:
            raise ValueError("User must attend the event before reviewing")

        if not 'rate' or not 'comment' in request.data:
            raise ValueError("All required fields must be input")

        if request.data['rate'] > 5 or request.data['rate'] < 0:
            raise ValueError("Rating must be between 1 and 5")

        if not request.data['comment']:
            raise ValueError("Comment must be input")

        
        Review.objects.create(
            event = checkEvent[0],
            attendee = attendee,
            rate = request.data['rate'],
            comment = request.data['comment']
        )

        return Response({
            "success":True,
            "message":"Successfully Reviewed the event " + str(checkEvent[0].name)
        })
    
    @action(detail=True,methods=['GET'])
    def getEventReviews(self,request,pk=None,format=None):
        
        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkReview = Review.objects.filter(event = checkEvent[0])
        if not checkReview.exists():
            return Response({
                "success":False,
                "message":"No reviews for user",
                "data":[]
            })

        allReviews = []
        average = 0
        length = 0

        for review in checkReview:
            singleReview = {}

            length = length + 1
            average = ((average*length-1) + review.rate)/length

            singleReview['attendeeUsername'] = review.attendee.username
            singleReview['attendeeId'] = review.attendee.pk
            singleReview['rate'] = review.rate
            singleReview['comment'] = review.comment
            singleReview['createdAt'] = review.timestamp

            allReviews.append(singleReview)
        return Response({
            "success":True,
            "message":"Found reviews for event",
            "data":allReviews,
            "averageRating":average
        })
    
    @action(detail=True,methods=['PUT'])
    def hideEvent(self,request,pk=None,format=None):
        
        admin = extractToken.checkAdminToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        if checkEvent[0].isHidden == True:
            raise ValueError("Event is already hidden")
        
        checkEvent.update(
            isHidden = True
        )

        return Response({
            "status":True,
            "message":"Successfully hidden the event"
        })
    
    @action(detail=True,methods=['PUT'])
    def unhideEvent(self,request,pk=None,format=None):

        admin = extractToken.checkAdminToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk )
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        if checkEvent[0].isHidden == False:
            raise ValueError("Event is not hidden")
        
        checkEvent.update(
            isHidden = False
        )

        return Response({
            "status":True,
            "message":"Succesfully unhidden the event"
        })
    
    @action(detail=False,methods=['GET'])
    def getHiddenEvents(self,request,format=None):

        admin = extractToken.checkAdminToken(request.headers)

        hiddenEvents = Event.objects.filter(isHidden__in = [True])

        if not hiddenEvents.exists():
            return Response({
                "status":False,
                "message":"No Hidden events found",
                "data":[]
            })
        
        allEvents = []
        for event in hiddenEvents:
            singleEvent = {}
            singleEvent['id'] = event.pk
            singleEvent['name'] = event.name
            singleEvent['startDate'] = event.startDate
            singleEvent['endDate'] = event.endDate
            singleEvent['description'] = event.description

            allEvents.append(singleEvent)


        return Response({
            "Success":True,
            "message":"Found hidden Events",
            "data":allEvents
        })
    
    @action(detail=True,methods=['GET'])
    def getEventReferralLink(self,request,pk=None,format = None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        checkEvent = Event.objects.filter( pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkReferral =  Referral.objects.filter(event = checkEvent[0],user = attendee)
        if not checkReferral.exists():
            code = utils.randomCodeGenerator(10)
            createdReferral= Referral.objects.create(
                event = checkEvent[0],
                user = attendee,
                code = code
            )
            userReferralLink = request.get_host() +'/event-invite/'+createdReferral.code
            return Response({
                "Success":True,
                "link":userReferralLink
            })
        
        userReferralLink = request.get_host() + '/event-invite/' + checkReferral[0].code

        return Response({
            "Success":True,
            "link":userReferralLink
        })

    @action(detail= True,methods= ['GET'])
    def getPromoCodeForEvent(self,request,pk = None , format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        if organizer != checkEvent[0].createdBy:
            raise ValueError("Not allowed")

        checkPromoCode = PromoCode.objects.filter(event_id = pk)

        if not checkPromoCode.exists():
            return Response({
                "success":False,
                "data":{}
                })

        return Response({
            "success":True,
            "data":{
                "code" : checkPromoCode[0].code,
                "event_id": checkPromoCode[0].event.id,
                "percentage_decrease": checkPromoCode[0].percentage_decrease,
                "dateCreated": str(checkPromoCode[0].dateCreated),
                "maxNoOfAttendees": checkPromoCode[0].maxNoOfAttendees
            }
        })

    @action(detail = True,methods = ['POST'])
    def createPromoCodeForEvent(self,request,pk = None , format = None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)

        code = None

        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        if organizer != checkEvent[0].createdBy:
            raise ValueError("Not allowed")
        
        checkPromoCode = PromoCode.objects.filter(event_id = pk)

        if checkPromoCode.exists():
            raise ValueError("Promo code for the event already exists")

        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Event has already been completed")

        if 'percentage_decrease' not in request.data.keys() or 'max_attendees' not in request.data.keys():
            raise ValueError("All required fields must be input.")
        
        if not isinstance(request.data['percentage_decrease'],float) and not isinstance(request.data['percentage_decrease'],int):
            raise ValueError("Percentage decrease must be a number.")
        
        if not isinstance(request.data['max_attendees'],int):
            raise ValueError("Maximum attendees must be an integer")
        
        if request.data['percentage_decrease'] > 50 or request.data['percentage_decrease'] <= 0:
            raise ValueError("Percentage decrease must be between 0 and 50")
        
        if 'code' in request.data.keys():
            code = request.data['code']
        else:
            code = utils.randomCodeGenerator(5)

        createdPromoCode = PromoCode.objects.create(
            code = code,
            event = checkEvent[0],
            percentage_decrease = request.data['percentage_decrease'],
            maxNoOfAttendees = request.data['max_attendees']
        )

        return Response({
            "success":True,
            "message":"Succesfully created the promo code",
            "code":createdPromoCode.code
        })    

    
    @action(detail=True,methods= ['GET'])
    def getEventViewsByMonth(self,request,pk = None,format = None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        if checkEvent[0].createdBy != organizer:
            raise ValueError("Not allowed.")
            
        checkEventViews = EventSeen.objects.filter(event = checkEvent[0])
        
        return Response({
            "success":True,
            "data":utils.dataAnalyticsFormatter(checkEventViews,'timestamp')
        })
    
    @action(detail=True,methods=['GET'])
    def getLikesByMonth(self,request, pk = None, format = None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        if checkEvent[0].createdBy != organizer:
            raise ValueError("Not allowed.")
        
        checkEventLikes = EventLike.objects.filter(event = checkEvent[0])

        return Response({
            "success":True,
            "data":utils.dataAnalyticsFormatter(checkEventLikes,'timestamp')
        })
    
    @action(detail=True,methods=['GET'])
    def getSharesByMonth(self,request,pk = None,format = None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkShares = Referral.objects.filter(event = checkEvent[0])

        return Response({
            "success":True,
            "data":utils.dataAnalyticsFormatter(checkShares,'createdAt')
        })

    @action(detail=True,methods=['GET'])
    def getAgeVarianceForBookers(self,request,pk = None,format = None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkEvent = Event.objects.filter(pk = pk)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkBookings = Booking.objects.filter(event = checkEvent[0])
        
        bookers = ExtendedUser.objects.filter(id__in = [cb.attendee.id for cb in checkBookings])

        return Response({
            "success":True,
            "data":utils.getAgeRange(bookers)
        })

    # endpoint to book events with-out account
    @action(detail=True,methods=['POST'])
    def bookEventWithOutAccount(self,request,pk=None,format=None):
        
        if not 'phone' or not 'email' or not 'first_name' or not 'last_name' in request.data.keys():
            raise ValueError("All required user-fields must be input")     
        
        if request.data['phone'][:1] != '+':
            raise ValueError("Phone No must be in correct format")
        
        checkUserPhone = ExtendedUser.objects.filter(phone = request.data['phone'])
        if checkUserPhone.exists():
            raise ValueError("User account with the phone no already exists.")
        
        checkUseremail = ExtendedUser.objects.filter(email = request.data['email'])
        if checkUseremail.exists():
            raise ValueError("User account with the email already exists.")
        
        checkEvent = Event.objects.filter(pk=pk)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Event has already ended")

        if not 'type' or not 'number' in request.data:
            raise ValueError("All required fields must be input")
        
        if not request.data['type'] in ['N','V','VV']:
            raise ValueError("Type not allowed")

        if not isinstance(request.data['number'],int):
            raise ValueError("Invalid number")
        
        if request.data['number'] < 1 or request.data['number'] > 10:
            raise ValueError("Bookings should be between 1 and 10")
        
        totalPrice = 0
        if request.data['type'] == 'V':
            if checkEvent[0].vipPrice == 0:
                raise ValueError("Vip does not exist for event")
            totalPrice = checkEvent[0].vipPrice * request.data['number']
        elif request.data['type'] == 'VV':
            if checkEvent[0].vvipPrice == 0:
                raise ValueError("VVip does not exist for event")
            totalPrice = checkEvent[0].vvipPrice * request.data['number']
        else:
            if checkEvent[0].normalPrice == 0 and request.data['number'] != 0:
                raise ValueError("Event is free ")
            totalPrice = checkEvent[0].normalPrice * request.data['number']
        
        password = utils.randomCodeGenerator(8)
        try:
            getToken = firebase_authentication.CreateUserInFirebase(request.data['email'], password, request.data['phone'])
        except Exception as e:
            print('Exception type '+str(e))
            raise ValueError("Invalid input for Firebase Usermanagement")

        try:
            createdUser = ExtendedUser.objects.create(
                phone= request.data['phone'],
                username = request.data['phone'],
                email = request.data['email'],
                first_name = request.data['first_name'],
                last_name = request.data['last_name'],
                links = [],
                firebase_uuid = getToken,
                profile_completed = False
            )

        except Exception as e:
            print('Exception type '+str(e))
            raise ValueError("Invalid input")

        createdUser.set_password(password)
        createdUser.save()
        
        checkBooking = Booking.objects.filter(attendee = createdUser,event = checkEvent[0])
        if checkBooking.exists():
            if checkBooking[0].is_verified == True:
                raise ValueError("User already booked for this event")
            else:
                checkBookingPayment = BookingPayment.objects.filter(booking = checkBooking[0])
                if checkBookingPayment.exists():
                    checkBookingPayment.delete()
                checkBooking.delete()
               
        userSerialzier = UserSerialzier(createdUser,many=False,context={'request': request})
        refresh = RefreshToken.for_user(createdUser)
 

        code = utils.randomCodeGenerator(10)
        item = "User "+str(createdUser.pk) +" booking event "+str(checkEvent[0].pk)
        checkoutUrl,transactionNo = telebirrConnector.bookWithTelebirr(totalPrice,item)

        context = {}
        factory = qrcode.image.svg.SvgImage
        img = qrcode.make(code,image_factory=factory,box_size=40)
        
        stream = BytesIO()
        img.save(stream)

        
        uploadedfile = cloudinary.uploader.upload(
            stream.getvalue(), 
            folder = "MinAleAddis/QRCodes/", 
            public_id = code+'qrcode',
            overwrite = True,  
            resource_type = "image"
        )

        createdBooking = Booking.objects.create(
            attendee = createdUser,
            event = checkEvent[0],
            type = request.data['type'],
            number = request.data['number'],
            code = code,
            qrcode = uploadedfile['url'],
            is_verified = False
        )

        createdBookingPayment = BookingPayment.objects.create(
            transactionNo = transactionNo,
            booking = createdBooking,
            amount = totalPrice
        )
        #Generate QR-Code with information
        factory = qrcode.image.svg.SvgImage
        generated_string = str(pk)+';'+'bought'+';'+str(createdBooking.id)+';'+request.data['first_name']+';'+request.data['last_name']+';'+request.data['phone']
        img = qrcode.make(generated_string, image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        
        # send event QR-code to email 
        attachments = []
        attachments.append(('event-booking-qrcode.SVG', stream.getvalue(), 'application/image'))
        html_template = 'event_booking_mail.html'
        html_message = render_to_string(html_template, {
            "image_url": createdBooking.qrcode,
            'title' : checkEvent[0].name,
            'description' : checkEvent[0].description,
            'venue' : checkEvent[0].venue,
            'price' : checkEvent[0].normalPrice,
            'username': createdUser.username,
            'email': createdUser.email,
            'first_name': createdUser.first_name,
            'last_name': createdUser.last_name,
            'phone': createdUser.phone,
            'password': password,
            'start_date' : checkEvent[0].startDate.strftime('%B %d, %Y'),
            'end_date' : checkEvent[0].endDate.strftime('%B %d, %Y'),
            'start_time' : checkEvent[0].startDate.strftime('%H:%M:%S'),
            'end_time' : checkEvent[0].endDate.strftime('%H:%M:%S'),
            'code' : None
        })
        message = EmailMessage('MnAle-Addis Event Booking', html_message, settings.EMAIL_HOST_USER, [ createdUser.email], attachments=attachments)
        message.content_subtype = 'html'
        message.send()
        
        return Response({
            "success":True,
            "message":"Confirm the booking with the Url sent.",
            "data":{
                "checkout_url":checkoutUrl['data']['toPayUrl'],
                "booking_id":createdBooking.pk,
                "amount":totalPrice,
                "QRCode" : uploadedfile['url'],
            },
            "user":userSerialzier.data,
            "token":{
                "refresh":str(refresh),
                "access":str(refresh.access_token)
            }
        })
    
    # endpoint to get event by private Event Key
    @action(detail = True, methods = ['GET'])
    def getPrivateEventByKey(self, request , pk = None, format = None):

        checkEvent = Event.objects.filter(prvt_evnt_key=pk)
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        return Response({
            "status":True,
            "message":"Successfully found the event",\
            "event":{
                'id': checkEvent[0].id,
                'name':checkEvent[0].name,
                'normalPrice':checkEvent[0].normalPrice,
                'vipPrice':checkEvent[0].vipPrice,
                "vvipPrice":checkEvent[0].vvipPrice,
                "description":checkEvent[0].description,
                "startDate": checkEvent[0].startDate,
                "endDate": checkEvent[0].endDate,
                "venue": checkEvent[0].venue,
                # "subCategory":checkEvent[0].subCategory,
                "location":checkEvent[0].location,
                "tags":checkEvent[0].tags,
                "phones":checkEvent[0].phones,
                "image_url":checkEvent[0].image_url,
                "createdBy":checkEvent[0].createdBy.first_name,
                "dressingCode":checkEvent[0].dressingCode,
                "maxNoOfAttendees":checkEvent[0].maxNoOfAttendees,
                "noOfViews":checkEvent[0].noOfViews,
                "isHidden":checkEvent[0].isHidden,
                "isVirtual":checkEvent[0].isVirtual,
                "prvt_evnt_key":checkEvent[0].prvt_evnt_key,
                "phone":checkEvent[0].phone,
                "org_name":checkEvent[0].org_name,
                "email":checkEvent[0].email,
                "isPrivate":checkEvent[0].isPrivate,
                "isActive":checkEvent[0].isActive
            }
        })

    # endpoint to reserve events with-out account
    @action(detail=True,methods=['POST'])
    def reserveEventWithOutAccount(self,request,pk=None,format=None):

        if not 'phone' or not 'email' or not 'first_name' or not 'last_name' in request.data.keys():
            raise ValueError("All required user-fields must be input")     
        
        phone = request.data['phone']
        if phone[0] != '0':
            phone = '0' + phone

        try:
            int(request.data['phone'])
        except ValueError:
            raise ValueError("Phone No must be an integer")
        if len(request.data['phone']) < 9:
            raise ValueError("Phone No can not be less than 9 digits")
        # if request.data['phone'][:1] != '+':
        #     raise ValueError("Phone No must be in correct format")
        
        phone = request.data['phone']
        if phone[0] != '0':
            phone = '0' + phone

        checkUserPhone = ExtendedUser.objects.filter(phone = phone)
        if checkUserPhone.exists():
            raise ValueError("User account with the phone no already exists.")
        
        checkUseremail = ExtendedUser.objects.filter(email = request.data['email'])
        if checkUseremail.exists():
            raise ValueError("User account with the email already exists.")
        
        checkEvent = Event.objects.filter(prvt_evnt_key=pk)
        print(pk)
        
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        # if checkEvent[0].normalPrice != 0 or checkEvent[0].vipPrice or checkEvent[0].vvipPrice:
        #     raise ValueError("Only free events are allowed")
        
        if checkEvent[0].endDate < timezone.now():
            raise ValueError("Event has already ended")

        if not 'number' in request.data:
            raise ValueError("All required fields must be input")
        
        if not isinstance(request.data['number'],int):
            raise ValueError("Invalid number")
        
        if request.data['number'] < 1 or request.data['number'] > 10:
            raise ValueError("Reservations should be between 1 and 10")
        
        if request.data['number'] > checkEvent[0].maxNoOfAttendees:
            raise ValueError("No reservation spots left for this number.")

        password = utils.randomCodeGenerator(8)
        
        try:
            getToken = firebase_authentication.CreateUserInFirebase(request.data['email'], password, phone)
        except:
            raise ValueError("Invalid input for Firebase Usermanagement")

        try:
            createdUser = ExtendedUser.objects.create(
                phone= phone,
                username = request.data['phone'],
                email = request.data['email'],
                first_name = request.data['first_name'],
                last_name = request.data['last_name'],
                links = [],
                firebase_uuid = getToken,
                profile_completed = False
            )

        except:
            raise ValueError("Invalid input")

        createdUser.set_password(request.data['email'])
        createdUser.save()
        
        userSerialzier = UserSerialzier(createdUser,many=False,context={'request': request})
        refresh = RefreshToken.for_user(createdUser)

        checkReservation = Reservation.objects.filter(attendee = createdUser,event = checkEvent[0])

        if checkReservation.exists():
            raise ValueError("User already reserved for this event")

        checkEvent.update(
            maxNoOfAttendees = checkEvent[0].maxNoOfAttendees - int(request.data['number'])
        )

        # if not (4 + timezone.now().day) < (checkEvent[0].startDate.day):
        #     raise ValueError("Can only reserve events before 4 days of the starting date") 
        
        createdReservation = Reservation.objects.create(
            attendee = createdUser,
            event = checkEvent[0],
            number = request.data['number']
        )

        #Generate QR-Code with information
        factory = qrcode.image.svg.SvgImage
        generated_string = str(pk)+';'+'bought'+';'+str(createdReservation.id)+';'+request.data['first_name']+';'+request.data['last_name']+';'+request.data['phone']
        img = qrcode.make(generated_string, image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        
        # properties to be sent via email
        # print(checkEvent[0].startDate|date:"g:i a")

        # send event QR-code to email
        attachments = []
        attachments.append(('event-reserving-qrcode.SVG', stream.getvalue(), 'application/image'))
        html_template = 'event_booking_mail.html'
        html_message = render_to_string(html_template, {
            "code": checkEvent[0].prvt_evnt_key,
            'img_url':checkEvent[0].image_url, 
            'title': checkEvent[0].name,
            'created_by' : checkEvent[0].org_name,
            'description': checkEvent[0].description,
            'start_date': checkEvent[0].startDate.strftime('%B %d, %Y'),
            'end_date':checkEvent[0].endDate.strftime('%B %d, %Y'),
            'start_time': checkEvent[0].startDate,
            'end_time':checkEvent[0].endDate,
            'link':'https://app.mnaleaddis.com/events/{}'.format(checkEvent[0].prvt_evnt_key),
            'price': checkEvent[0].normalPrice,
            'venue': checkEvent[0].venue
            })

        message = EmailMessage(
            'MnAle-Addis Event Reserving', 
            html_message, 
            settings.EMAIL_HOST_USER, 
            [ createdUser.email],
            attachments=attachments
        )

        message.content_subtype = 'html'
        message.send()
        remail = createdUser.email
        firebase_authentication.reset_password(remail)

        return Response({
            "status":True,
            "message":"Succesfully made the reservation",
            "data":{
                "reservation_id":createdReservation.pk,
                "space_left":createdReservation.event.maxNoOfAttendees
            },
            "user":userSerialzier.data,
            "token":{
                "refresh":str(refresh),
                "access":str(refresh.access_token)
            }
        })
    
    # removed soon, only for test 
    @action(detail=False,methods=['POST'])
    def check_email_send(self, request, format=None):
        #Generate QR-Code with
        factory = qrcode.image.svg.SvgImage
        generated_string = str(1)+';'+'bought'+';'+str(11)+';'+'first_name'+';'+'last_name'+';'+'phone'
        img = qrcode.make(generated_string, image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        
        # send event QR-code to email
        attachments = []
        attachments.append( ('filename.SVG', stream.getvalue(), 'application/image'))
        print(len(attachments))
        # print(attachments[0])
        html_template = 'html.html'
        html_message = render_to_string(html_template, {"image_url": 'https://www.w3schools.com/html/pic_trulli.jpg'})
        message = EmailMessage('MnAle-Addis Event Booking', html_message, settings.EMAIL_HOST_USER, [ 'amanuelasfawdeveloper@gmail.com','amanuelasfawardi@gmail.com'], attachments=attachments)
        message.content_subtype = 'html'
        message.send()
        
        return Response({
            "success":True,
            "message":"Email send success"
        })
    
    # end-point to Private-Event Create by Admin
    @action(detail=False,methods=['POST'])
    def privateEventCreateByAdmin(self,request,format=None):
                
        if not 'org_email' in request.data.keys() and not 'org_phone' in request.data.keys() and 'org_name' in request.data.keys():
            raise ValueError("All Organizer info required fields must be input")

        organizer = ExtendedUser.objects.filter(phone=request.data['org_phone'],email = request.data['org_email'], is_staff=True).first()

        if organizer == None:
            organizer = extractToken.checkAdminToken(request.headers)

        #check the required variables are input
        names = ('name','normalPrice','phones','venue','description','startDate','location','tags','maxNoOfAttendees','sub-category')
        if not all(name in request.data.keys() for name in names):
            raise ValueError("All required fields must be input")

        #check the request body is not of string value
        if isinstance(request.data,str):
            raise ValueError("All required fields must be input")
        #check the tags value is a list    
        if not isinstance(request.data['tags'],list):
            raise ValueError("Tags must be an array")
        #check the phones values is a list
        if not isinstance(request.data['phones'],list):
            raise ValueError("Phones must be an array")
        # check the sub-category is of type
        if not isinstance(request.data['sub-category'],int):
            raise ValueError("Sub Category Id must be an integer")

        checkSubCategory = SubCategory.objects.filter(pk = request.data['sub-category'])
        if not checkSubCategory.exists():
            raise ValueError("Sub category does not exist with the id entered")
        
        # subCategorySerializer = SubCategorySerializer(checkSubCategory,many=False,context={'request': request})
        # print(subCategorySerializer.data)
        if not utils.is_datetime(datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M')):
            raise ValueError("Invalid start date format")
        if datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M') < datetime.now():
            raise ValueError("Start Date can not be before the Current time and date")

        if 'endDate' in request.data:
            if not utils.is_datetime(datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M')):
                raise ValueError("Invalid end date format")
            if datetime.strptime(request.data['endDate'],'%Y-%m-%d %H:%M') < datetime.strptime(request.data['startDate'],'%Y-%m-%d %H:%M'):
                raise ValueError("End date must be after the start Date")

        # if 'sub-category'
        if not type(request.data['maxNoOfAttendees'] == int):
            raise ValueError("Attendee must be an integer")
        if not request.data['name'] or not request.data['description']:
            raise ValueError("All required fields must be input")
        if not type(request.data['normalPrice']) == int and not type(request.data['normalPrice']) == float:
            raise ValueError("Price must be a number")
        if 'vipPrice' in request.data:
            if not type(request.data['vipPrice']) == int and not type(request.data['vipPrice']) == float:
                raise ValueError("vipPrice must be a number")
            if request.data['vipPrice'] < 0:
                raise ValueError("Price can not be less than 0")
        if 'vvipPrice' in request.data:
            if not type(request.data['vvipPrice']) == int and not type(request.data['vvipPrice']) == float:
                raise ValueError("vvipPrice must be a number")
            if request.data['vvipPrice'] < 0:
                raise ValueError("Price can not be less than 0")
        if 'dressingCode' in request.data:
            if not request.data['dressingCode']:
                raise ValueError("Dressing Code can not be empty")
        if 'venue' in request.data:
            if not request.data['venue']:
                raise ValueError("Venue can not be empty")
        if request.data['normalPrice'] < 0:
            raise ValueError("Price can not be less than 0")
        
        tags = []
        for tag in request.data['tags']:
            if tag[0] != '#':
                tags.append('#' + tag)
            else:
                tags.append(tag)
            # tags.append(TagSerializer(tagObject[0],context={'request':request}).data['url'])

        # private event key
        priate_event_key = utils.randomCodeGenerator(6)
        
        data = {}
        
        data['name'] = request.data['name']
        data['normalPrice'] = request.data['normalPrice']
        data['description'] = request.data['description']
        data['startDate'] = request.data['startDate']
        data['phones'] = request.data['phones']
        data['maxNoOfAttendees'] = request.data['maxNoOfAttendees']
        data['venue'] = request.data['venue']
        # data['subCategory'] = subCategorySerializer.data['url']
        if 'endDate' in request.data:
            data['endDate'] = request.data['endDate']
        if 'vipPrice' in request.data:
            data['vipPrice'] = request.data['vipPrice']
        if 'vvipPrice' in request.data:
            data['vvipPrice'] = request.data['vvipPrice']
        if 'dressingCode' in request.data:
            data['dressingCode'] = request.data['dressingCode']
        data['location'] = request.data['location']
        data['tags'] = tags
        data['createdBy'] = organizer.pk
        data['isPrivate'] = True
        data['prvt_evnt_key'] = priate_event_key
        data['email'] = request.data['org_email']
        data['phone'] = request.data['org_phone']
        data['org_name'] = request.data['org_name']
        
        serializer = EventSerializer(data= data,context={'request': request})
        if not serializer.is_valid():
            return Response({
                "success":False,
                "message":serializer.errors,
                "data":{}
            })
        
        serializer.save()
        
        """ 
        getCreatedEvent = Event.objects.filter(pk= serializer.data['id'])
        getCreatedEvent.update(
            subCategory = checkSubCategory[0]
        )
        
        signals.notify_followers.send(sender="Event-Creation",event=getCreatedEvent[0],organizer=organizer)
        signals.notify_interested.send(sender="Event-Creation",event=getCreatedEvent[0],organizer=organizer)
        """
        
        return Response({
            "status":True,
            "message":"Successfully Created the Private-Event",
            "data":serializer.data
        })
    

    # end-point to Add list of Attendee to private-event by Admin
    @action(detail=True,methods=['POST'])
    def addAttendeesToPrivateEventByAdmin(self,request,pk=None,format=None):
        
        organizer = extractToken.checkAdminToken(request.headers)

        # add attendees to private event attendee list
        event = Event.objects.filter(pk=pk, isPrivate=True).first()
        if event is None:
            raise ValueError("Event not found")

        names = ['attendee_list']
        if not all(name in request.data.keys() for name in names):
            raise ValueError("All required fields must be input")

        if not len(request.data['attendee_list']) > 0 or request.data['attendee_list'] == None:
            raise ValueError("List of Attendees not found")

        for attendee in request.data['attendee_list']:
            attendee_params = ['phone', 'email']
            if not all(param in attendee.keys() for param in attendee_params):
                raise ValueError('Attendee List must contain all required input field.')

        attendee_list_to_send = []
        for attendee in request.data['attendee_list']:
            exist_attendee = EventAttendee.objects.filter(event=event, phone=attendee['phone'], email=attendee['email']).first()
            if exist_attendee is None:
                EventAttendee.objects.create(
                    event = event,
                    phone = attendee['phone'],
                    name = attendee['name'],
                    email = attendee['email']
                )
                attendee_list_to_send.append(attendee)

        
        attendee_list_to_send = EventAttendee.objects.filter(event=event)
        serialized_attendee_list_to_send = EventAttendeeSerializer(attendee_list_to_send, many=True).data
        
        return Response({
            "success":True,
            "message":"Add Attendees to the invitation list success",
            'exist_attendee' : serialized_attendee_list_to_send
        })


    # end-point to send invitation email to attendees in private event
    @action(detail=True,methods=['POST'])
    def sendPrivateEventInvitationEmail(self,request,pk=None,format=None):
        
        organizer = extractToken.checkAdminToken(request.headers)

        event = Event.objects.filter(pk=pk, isPrivate=True).first()
        if event is None:
            raise ValueError("Event not found")

        attendee_list_to_send = EventAttendee.objects.filter(event=event,isSend=False)
        
        serialized_attendee_list_to_send = EventAttendeeSerializer(attendee_list_to_send, many=True).data
        
        # send notification email to every attendees in the list
        for attendee in attendee_list_to_send:
            try:
                html_template = 'private_event_envitation_mail.html'
                html_message = render_to_string(html_template, {
                    "code": event.prvt_evnt_key,
                    'img_url':event.image_url, 
                    'title': event.name,
                    'created_by' : event.org_name,
                    'description': event.description,
                    'start_date': event.startDate.strftime('%B %d, %Y'),
                    'end_date':event.endDate.strftime('%B %d, %Y'),
                    'start_time': event.startDate.strftime('%H:%M:%S'),
                    'end_time':event.endDate.strftime('%H:%M:%S'),
                    'link':'',
                    'price': event.normalPrice,
                    'venue': event.venue
                    })
                message = EmailMessage('MnAle-Addis Private Event Invitation', html_message, settings.EMAIL_HOST_USER, [ attendee.email])
                message.content_subtype = 'html'
                message.send()
                event_ = Event.objects.get(pk=attendee.event.id)
                print(event_)
                attendee_cpy = EventAttendee(phone=attendee.phone, 
                    email=attendee.email, name=attendee.name, 
                    event=event_, isSend=True)

                
                EventAttendee.objects.filter(phone=attendee.phone, email=attendee.email).delete()

                attendee_cpy.save()
            except Exception as e:
                return Response({
                    "success":False,
                    "message":"Invitation Email send has Error",
                    "error" : str(e),
                    "attendee": EventAttendeeSerializer(attendee, many=False).data
                })

        attendee_list_to_send_ = EventAttendee.objects.filter(event=event)
        serialized_attendee_list_to_send = EventAttendeeSerializer(attendee_list_to_send_, many=True).data

        return Response({
            "success":True,
            "message":"Invitation Email send success",
            "attendees": serialized_attendee_list_to_send
        })

    # end-point to reset Private-Event attendee list
    @action(detail=True,methods=['POST'])
    def resetPrivateEventAttendeList(self,request,pk=None,format=None):
        
        organizer = extractToken.checkAdminToken(request.headers)
        
        event = Event.objects.filter(pk=pk, isPrivate=True).first()
        if event is None:
            raise ValueError("Event not found")
        
        EventAttendee.objects.filter(event=event).delete()
        
        attendee_list_to_send = EventAttendee.objects.filter(event=event)
        serialized_attendee_list_to_send = EventAttendeeSerializer(attendee_list_to_send, many=True).data
        
        return Response({
            "success":True,
            "message":"Private-Event Attende List reset success",
            'exist_attendee' : serialized_attendee_list_to_send
        })

    # get booking lists
    @action(detail=False,methods=['GET'])
    def getBookingList(self,request,pk = None,format = None):
        booking_list = BookingPayment.objects.all()

        serialized_data = BookingPaymentSerializer(booking_list, many=True).data

        return Response({
            "success":True,
            'booking_list' : serialized_data
        })

    # get booking lists
    @action(detail=True,methods=['GET'])
    def getBookingDetail(self,request,format=None):
        booking_list = Booking.objects.get(pk=pk)

        serialized_data = BookingSerializer(booking_list, many=False).data

        return Response({
            "success":True,
            'booking_data' : serialized_data
        })

