from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from app.models import *
from app.serializers import *
from app.scripts import extractToken



class AdminViewSet(viewsets.ModelViewSet):
    queryset = ExtendedUser.objects.filter(is_staff=True)
    serializer_class = UserSerialzier

    @action(detail=False,methods=['POST'])
    def signin(self,request,format=None):
        
        if not 'username' or not 'password' in request.data.keys():
            raise ValueError("Keys are required")

        user = ExtendedUser.objects.get(username = request.data['username'])
        if not user.check_password(request.data['password']):
            raise ValueError("Invalid Credentials")

        if user == None or user.is_staff != True:
            raise ValueError("Invalid credentials")

        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh':str(refresh),
            'access':str(refresh.access_token)
        })   
    
    @action(detail=False,methods=['PUT'])
    def editPassword(self,request,format = None):
        admin = extractToken.checkAdminToken(request.headers)

        fields = ('oldPassword','newPassword')
        if not all(name in request.data.keys() for name in fields):
            raise ValueError("All required fields must be input")

        
        oldPassword = request.data['oldPassword']
        newPassword = request.data['newPassword']

        if oldPassword == newPassword:
            raise ValueError("Old and new passwords must be different")

        if len(newPassword) < 6:
            raise ValueError("Password length must be 6 or more characters")
        
        if not admin.check_password(oldPassword):
            raise ValueError("Error in changing Password")
        
        admin.set_password(newPassword)
        admin.save()

        return Response({
            "success":True,
            "message":"Succesfully updated the password"
        })

    @action(detail=False,methods=['PUT'],url_path=r'deactivateUser/(?P<user_id>\d+)')
    def deactivateUser(self,request,format=None,*args,**kwargs):
        
        admin = extractToken.checkAdminToken(request.headers)

        userId = kwargs['user_id']
        
        
        user = ExtendedUser.objects.filter(pk = userId)
        if not user.exists():
            raise ValueError("User does not exist")

        if user[0].isBlocked:
            raise ValueError("User is already blocked")
        user.update(
            isBlocked = True
        )
        return Response({
            "success":True,
            "message":"Succesfully deactivated the user " + str (user[0].username)
        })
    
    @action(detail=False,methods=['PUT'],url_path=r'activateUser/(?P<user_id>\d+)')
    def activateUser(self,request,format=None,*args,**kwargs):
        
        admin = extractToken.checkAdminToken(request.headers)

        userId = kwargs['user_id']
        user = ExtendedUser.objects.filter(pk = userId)

        if not user.exists():
            raise ValueError("User does not exist")
        
        if not user[0].isBlocked:
            raise ValueError("User is not blocked")

        user.update(
            isBlocked = False
        )

        return Response({
            "success":True,
            "message":"Succesfully reactivated the user " + str (user[0].username)
        })

    @action(detail=False,methods=['GET'])
    def getOrganizerVerificationRequests(self,request,format=None):

        admin = extractToken.checkAdminToken(request.headers)

        verificationRequests = OrganizerDetail.objects.filter(isVerified = False,kebele_image_url1__isnull = False,kebele_image_url2__isnull = False)
        print(verificationRequests)

        if not verificationRequests.exists():
            return Response(
                {
                    "success":False,
                    "data":[]
                })
        allRequests = []
        for request in verificationRequests:
            singleRequest = {}
            singleRequest['organizer_id'] = request.organizer.id
            singleRequest['first_name'] = request.organizer.first_name[0],
            singleRequest['last_name'] = request.organizer.last_name
            singleRequest['kebele_id1'] = request.kebele_image_url1
            singleRequest['kebele_id2'] = request.kebele_image_url2

            

            allRequests.append(singleRequest)


        return Response({
            "success":True,
            "data":allRequests
        })

    @action(detail=False,methods=['PUT'],url_path=r'verifyOrganizer/(?P<organizer_id>\d+)')
    def verifyOrganizer(self,request,format=None,*args, **kwargs):
        
        admin = extractToken.checkAdminToken(request.headers)
        organizerId = kwargs['organizer_id']

        organizer = ExtendedUser.objects.filter(pk = organizerId)

        if not organizer.exists() or organizer[0].isOrganizer == False:
            raise ValueError("Organizer with the Id does not exist")
        
        checkDetails = OrganizerDetail.objects.filter(organizer = organizer[0])
        if not checkDetails.exists():
            raise ValueError("Organizer does not have a verification request")
        
        if checkDetails[0].isVerified == True or checkDetails[0].kebele_image_url1 == None or checkDetails[0].kebele_image_url2 == None:
            raise ValueError("Not valid request by organizer")

        checkDetails.update(
            isVerified = True
        )
        return Response({
            "success":True,
            "message":"Successfully Verified organizer"
        })
    
    @action(detail=False,methods=['POST'])
    def createWalletConfig(self,request,format = None):
        admin = extractToken.checkAdminToken(request.headers)

        if 'coinPerSurvey' not in request.data.keys() or 'coinPerEvent' not in request.data.keys() or 'coinToBirr' not in request.data.keys():
            raise ValueError("All required fields must be input")
        
        print(isinstance(request.data['coinPerSurvey'],int))
        if not isinstance(request.data['coinPerSurvey'],int) and not isinstance(request.data['coinPerSurvey'],float):
            raise ValueError("coinPerSurvey must be a number")

        print(isinstance(request.data['coinPerSurvey'],int))
        if not isinstance(request.data['coinPerEvent'],int) and not isinstance(request.data['coinPerEvent'],float):
            raise ValueError("coinPerEvent must be a number")
        
        if not isinstance(request.data['coinToBirr'],int) and not isinstance(request.data['coinToBirr'],float):
            raise ValueError("coinToBirr must be a number")
        
        for key in request.data:
            if request.data[key] <= 0:
                raise ValueError("All properties must be greather than 0.")
        
        checkConfig = WalletConfig.objects.filter()
        if not checkConfig.exists():
            config = WalletConfig.objects.create(
                coinPerSurvey = request.data['coinPerSurvey'],
                coinPerEvent = request.data['coinPerEvent'],
                coinToBirr = request.data['coinToBirr']
            )

            return Response({
                "success":True,
                "message":"Successfully created the wallet config for users."
            })

        else:
            
            editedConfig = WalletConfig.objects.filter(pk = checkConfig[0].id).update(
                coinPerSurvey = float(request.data['coinPerSurvey']),
                coinPerEvent = request.data['coinPerEvent'],
                coinToBirr = request.data['coinToBirr']    
            )

            return Response({
                "success":True,
                "message":"Successfully edited the wallet config for users."
            })


    @action(detail=False,methods=['GET'])
    def privateEventList(self,request,format = None):
        admin = extractToken.checkAdminToken(request.headers)

        private_events = Event.objects.filter(isPrivate=True)
        
        serializer_context = {
            'request': request,
        }
        
        private_events_serialized = EventSerializer(private_events, many=True, context=serializer_context)
        return Response({
            "success":True,
            "event-list":private_events_serialized.data
        })

    # @action(detail=False,methods=['PUT'],url_path=r'deactivatePrivateEvent/(?P<event_id>\d+)')
    # def deactivatePrivateEvent(self,request,format=None,*args, **kwargs):
    @action(detail=True,methods=['PUT'])
    def deactivatePrivateEvent(self,request,pk=None,format=None):
        admin = extractToken.checkAdminToken(request.headers)
        event_id = pk

        event = Event.objects.get(pk=event_id)
        event.isActive = False
        event.save()
        
        serializer_context = {
            'request': request,
        }
        
        private_event_serialized = EventSerializer(event, many=False, context=serializer_context)
        
        return Response({
            "success":True,
            "message" : 'Event Deactivate Successfully.',
            "data":private_event_serialized.data
        })

        
    # @action(detail=False,methods=['PUT'],url_path=r'activatePrivateEvent/(?P<event_id>\d+)')
    # def activatePrivateEvent(self,request,format=None,*args, **kwargs):
    @action(detail=True,methods=['PUT'])
    def activatePrivateEvent(self,request,pk=None,format=None):
        admin = extractToken.checkAdminToken(request.headers)
        event_id = pk
        
        event = Event.objects.get(pk=event_id)
        event.isActive = True
        event.save()
        
        serializer_context = {
            'request': request,
        }
        
        private_event_serialized = EventSerializer(event, many=False, context=serializer_context)
        
        return Response({
            "success":True,
            "message" : 'Event Activate Successfully.',
            "data":private_event_serialized.data
        })

    @action(detail=False,methods=['GET'])
    def getAttendees(self,request,pk=None,format=None):
        attendees = ExtendedUser.objects.filter(email='')

        serializer_context = {
            'request': request,
        }
        
        serialized_data = UserSerialzier(attendees, many=True, context=serializer_context)

        
        return Response({
            "success":True,
            "user-list" : serialized_data.data,
            "count": len(serialized_data.data)
        })