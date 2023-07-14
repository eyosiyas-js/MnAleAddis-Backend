import calendar
# from crypt import methods
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from typing import List
from django.contrib.auth.models import User
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from app.models import *
from app.serializers import *
from app.scripts import utils,firebase

from app.scripts import extractToken
from app.signals import signals

import imghdr
import cloudinary,cloudinary.uploader,cloudinary.api

class AttendeeViewSet(viewsets.ModelViewSet):
 
    queryset = ExtendedUser.objects.filter(is_staff__in=[False],isOrganizer__in=[False])
    serializer_class = UserSerialzier

    def create(self,request,format=None):

        if not 'phone' or not 'email' or not 'sex' or not 'dateofbirth' or not 'username' or not 'first_name' or not 'last_name' or not 'password' or not 'idToken' in request.data.keys():
            raise ValueError("All required fields must be input")
                
        if request.data['phone'][:1] != '+':
            raise ValueError("Phone no must be in correct format")
        
        checkUser = ExtendedUser.objects.filter(phone = request.data['phone'])
        if checkUser.exists():
            raise ValueError("User account with the phone no already exists.")
        
        uuid = firebase.checkUserWithUUID(request.data['idToken'])

        try:
            createdUser = ExtendedUser.objects.create(
                phone= request.data['phone'],
                sex = request.data['sex'],
                username = request.data['username'],
                first_name = request.data['first_name'],
                last_name = request.data['last_name'],
                links = [],
                firebase_uuid = uuid,
                profile_completed = False
            )

        except:
            raise ValueError("Invalid input")

        createdUser.set_password(request.data['password'])
        createdUser.save()
        

        userSerialzier = UserSerialzier(createdUser,many=False,context={'request': request})
        refresh = RefreshToken.for_user(createdUser)

        return Response({
            "success":True,
            "message":"Attendee created successfully",
            "user":userSerialzier.data,
            "token":{
                "refresh":str(refresh),
                "access":str(refresh.access_token)
            }
        })
    
    def update(self, request, pk=None):


        checkAttendee = extractToken.checkAttendeeToken(request.headers)

        attendee = ExtendedUser.objects.filter(pk=pk)

        if not attendee.exists():
            raise ValueError("User does not exist")
        
        if checkAttendee.pk != attendee[0].pk:
            raise ValueError("Action not allowed")

        if attendee[0].isOrganizer or attendee[0].is_staff:
            raise ValueError("Action not allowed")

        if 'first_name' not in request.data.keys() or  'last_name' not in request.data.keys() or 'username' not in request.data.keys():
            raise ValueError("All required fields must be input")
        
        # if not request.data['first_name'] or not request.data['last_name'] or not request.data['username'] or not request.data['email'] or not request.data['phone'] :
        #     raise ValueError("All required fields must be input")

        attendee.update(
            first_name = request.data['first_name'],
            last_name = request.data['last_name'],
            username = request.data['username'],
        )

        return Response({
            "success":True,
            "message":"Succesfully updated the user",
            "user":{
                "first_name":attendee[0].first_name,
                "last_name":attendee[0].last_name,
                "username":attendee[0].username,
            }
        })
        # return super().update(request, pk=None)
    @action(detail=False,methods=['PUT'])
    def editPassword(self,request,format = None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        fields = ('oldPassword','newPassword')
        if not all(name in request.data.keys() for name in fields):
            raise ValueError("All required fields must be input")

        
        oldPassword = request.data['oldPassword']
        newPassword = request.data['newPassword']

        if oldPassword == newPassword:
            raise ValueError("Old and new passwords must be different")

        if len(newPassword) < 6:
            raise ValueError("Password length must be 6 or more characters")
        
        if not attendee.check_password(oldPassword):
            raise ValueError("Error in changing Password")
        
        attendee.set_password(newPassword)
        attendee.save()

        return Response({
            "success":True,
            "message":"Succesfully updated the password"
        })

    @action(detail=False,methods=['PUT'])
    def deactivateAccount(self,request,format=None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        getAttendee = ExtendedUser.objects.filter(pk = attendee.id)
        if getAttendee[0].isBlocked:
            raise ValueError("User account is already de-activated.")
        getAttendee.update(
            isBlocked = True
        )
        
        return Response({
            "success":True,
            "message":"Successfully de-activated account."
        })

    @action(detail=False,methods=['POST'])
    def signin(self,request,format=None):
        
        if not 'phone' in request.data.keys() or not 'password' in request.data.keys():
            raise ValueError("all keys are required")

        phone = request.data['phone']
        if len(phone) < 10:
            raise ValueError("phone must be 10 digits")
        # phone = phone[1:]    
        try:
            user = ExtendedUser.objects.get(phone = phone)
            if not user.check_password(request.data['password']):
                raise ValueError("Invalid Credentials")

            if user.isBlocked:
                    raise ValueError("Account is temporarily deactivated,contact admins")

            if user == None or user.is_staff != False or user.isOrganizer != False:
                raise ValueError("Invalid credentials")

            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh':str(refresh),
                'access':str(refresh.access_token)
            })
        except:
            raise ValueError("Invalid input")
            
    @action(detail = True,methods = ['PUT'])
    def uploadUserImage(self, request , format = None, pk = None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        profile = ExtendedUser.objects.filter( pk = attendee.id)
        # defines the allowed types for the event and 
        # checks the input image is in the in the allowed list of image types
        allowedTypes = ['png','jpg','jpeg']
        # checks if the image is present in the request files 
        if not 'image' in request.FILES.keys():
            if not 'image' in request.data.keys():
                raise ValueError("Image must be provided")

        if 'image' in request.FILES.keys():
            image = request.FILES['image']
            if imghdr.what(image) not in allowedTypes:
                raise ValueError("Image must of png,jpg or jpeg types")
        else:
            image = request.data['image']
        
        # uploads the image to cloudinary with the appropriate data
        uploadedFile = cloudinary.uploader.upload(
            image,
            folder = "MinAleAddis/Users/Images/",
            public_id = "User " + str(profile[0].pk) + " image",
            overwrite = True,
            resource_type = "image" 
        )

        # saves the image url to the user object
        profile.update(
            image_url = uploadedFile['url']
        )

        return Response({
            "success":True,
            "message":"Successfully uploaded the image for user" + str(profile[0].first_name) +" " + str(profile[0].last_name),
            "data":{
                "url": profile[0].image_url
            }
        })
        
    @action(detail = False,methods=['GET'])
    def getProfile(self,request , format = None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        profile = ExtendedUser.objects.get( pk = attendee.pk)

        return Response({
            "success":True,
            "profile":{
                "id":profile.pk,
                "first_name":profile.first_name,
                "last_name":profile.last_name,
                "username":profile.username,
                "dateofbirth":profile.dateofbirth,
                "image":profile.image_url,
                "phone":profile.phone,
                "email":profile.email,
            }
        })
    
    @action(detail=False,methods=['GET'])
    def getSavedEvents(self,request,format=None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        savedEvents = SavedEvent.objects.filter(attendee=attendee)
        if not savedEvents.exists():
            return Response({
                "status":False,
                "message":"No saved events found",
                "events":[]
            })

        allSavedEvents = []
        for event in savedEvents:
            
            allSavedEvents.append(event.event)

        return Response({
            "status":True,
            "message":"Found saved events",
            "events" : utils.eventFormatter(allSavedEvents)
        })
    
    @action(detail=False,methods=['PUT'])
    def formatEvent(self,request , format = None):
        getSavedEvents = SavedEvent.objects.all()

        for event in getSavedEvents:
            print(event.event.name)
            print(event.attendee)

        return Response({
            "success":True
        })

    @action(detail=False,methods=['PUT'],url_path=r'saveEvent/(?P<event_id>\d+)')
    def saveEvent(self,request,format=None,*args, **kwargs):
    
        
        attendee = extractToken.checkAttendeeToken(request.headers)
        if attendee.profile_completed == False:
            raise ValueError("Profile must be completed.")

        eventId = kwargs['event_id']
        checkEvent = Event.objects.filter(pk = eventId)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        checkSaved = SavedEvent.objects.filter(event = eventId ,attendee = attendee)
        if checkSaved.exists(): raise ValueError("Event has already been saved by the user")

        SavedEvent.objects.create(
            event = checkEvent[0],
            attendee = attendee
        )
        
        return Response({
            "status":True,
            "message":"Successfully saved the event for later."
        })
    
    @action(detail=False,methods=['PUT'],url_path=r'unSaveEvent/(?P<event_id>\d+)')
    def unSaveEvent(self,request,format=None, *args, **kwargs):
        attendee = extractToken.checkAttendeeToken(request.headers)

        eventId = kwargs['event_id']
        checkEvent = Event.objects.filter(pk = eventId)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        checkSaved = SavedEvent.objects.filter(event = eventId ,attendee = attendee)

        if not checkSaved.exists(): raise ValueError("Event has not been saved by the user")
        checkSaved.delete()

        return Response({
            "success":True,
            "message":"Successfully unsaved the event."
        })

    @action(detail=False,methods=['PUT'],url_path=r'likeEvent/(?P<event_id>\d+)')
    def likeEvent(self,request,format=None,*args, **kwargs):

        attendee = extractToken.checkAttendeeToken(request.headers)

        eventId = kwargs['event_id']
        checkEvent = Event.objects.filter(pk = eventId)
        if not checkEvent.exists():
            raise ValueError("Event does not exist")

        if attendee in checkEvent[0].likedBy.all():
            raise ValueError("Event already liked by user")
        checkEvent[0].likedBy.add(attendee)

        EventLike.objects.create(
            event = checkEvent[0],
            attendee = attendee
        )

        return Response({
            "success":True,
            "message":"Successfully like the event"
        })

    @action(detail=False,methods=['PUT'],url_path=r'unlikeEvent/(?P<event_id>\d+)')
    def unlikeEvent(self,request,format=None,*args, **kwargs):

        attendee = extractToken.checkAttendeeToken(request.headers)
        eventId = kwargs['event_id']
        checkEvent = Event.objects.filter(pk = eventId)

        if not checkEvent.exists():
            raise ValueError("Event does not exist")
        
        if attendee not in checkEvent[0].likedBy.all():
            raise ValueError("Event not liked by user")
        checkEvent[0].likedBy.remove(attendee)

        EventLike.objects.filter(event= checkEvent[0],attendee = attendee).delete()
        
        
        return Response({
            "success":True,
            "message":"Successfully unliked the event"
        })
    
    @action(detail=False,methods=['PUT'],url_path=r'confirmVisitLink/(?P<organizer_id>\d+)')
    def confirmVisitLink(self,request,format=None,*args,**kwargs):
        attendee = extractToken.checkAttendeeToken(request.headers)
        
        organizerId = kwargs['organizer_id']
        organizer = ExtendedUser.objects.filter(pk=organizerId)

        if not organizer.exists():
            raise ValueError("Organizer does not exist")
        if not organizer[0].isOrganizer:
            raise ValueError("Organizer does not exist")

        if 'link' not in request.data.keys():
            raise ValueError("link is required")
                
        if not organizer[0].links:
            raise ValueError("Organizer has no links.")
        
        checker = False
        allLinks = []
        for link in organizer[0].links:
            
            if link['link'] == request.data['link']:
                checker = True
                link['noOfViews'] = link['noOfViews'] + 1
            allLinks.append({
                "link":link['link'],
                "noOfViews":link['noOfViews']
            })
        if not checker:
            raise ValueError("Link not in organizer's added links")
        
        organizer.update(
            links = allLinks
        )
        return Response({
            "success":True
        })

    @action(detail=False,methods=['PUT'],url_path=r'followOrganizer/(?P<organizer_id>\d+)')
    def followOrganizer(self,request,format=None,*args, **kwargs):

        attendee = extractToken.checkAttendeeToken(request.headers)
        
        organizerId = kwargs['organizer_id']

        organizer = ExtendedUser.objects.filter(pk=organizerId)

        if (not organizer.exists()) or (not organizer[0].isOrganizer):
            raise ValueError("Organizer does not exist")

        checkOrganizer = OrganizerFollowing.objects.filter(attendeeId = attendee.pk,organizer = organizer[0])
        if checkOrganizer.exists():
            return Response({
                "success":"False",
                "message":"Already following " + str(organizer[0].username)
            })
        
        OrganizerFollowing.objects.create(
            attendeeId = attendee.pk,
            organizer = organizer[0]
        )
        
        signals.notify_organizer_following.send(
            sender="attendee-following",
            attendee = attendee,
            organizer = organizer[0]
        )

        return Response({
            "Success":True,
            "message":"Successfully followed " + str(organizer[0].username)
        })
    
    @action(detail=False,methods=['PUT'],url_path=r'unfollowOrganizer/(?P<organizer_id>\d+)')
    def unfollowOrganizer(self,request,format=None,*args, **kwargs):
        attendee = extractToken.checkAttendeeToken(request.headers)
        
        organizerId = kwargs['organizer_id']
        organizer = ExtendedUser.objects.filter(pk=organizerId)

        if (not organizer.exists()) or (not organizer[0].isOrganizer):
            raise ValueError("Organizer does not exist")
        
        checkOrganizer = OrganizerFollowing.objects.filter(attendeeId = attendee.pk,organizer = organizer[0])
        if not checkOrganizer.exists():
            return Response({
                "Success":False,
                "message":"Organizer not followed"
            })
        checkOrganizer.delete()

        return Response({
            "Success":True,
            "message":"Succesfully unfollowed the organizer "+ str(organizer[0].username)
        })

    @action(detail=False,methods=['GET'])
    def getFollowing(self,request,format=None):

        attendee = extractToken.checkAttendeeToken(request.headers)

        checkOrganizers = OrganizerFollowing.objects.filter(attendeeId = attendee.pk)
        if not checkOrganizers.exists():
            return Response({
                "success":False,
                "message":"Found no followed organizers",
                "data":[]

            })
        
        following = []
        for organizer in checkOrganizers:
            data = {}
            
        
            data['username'] = organizer.organizer.username
            data['first_name'] = organizer.organizer.first_name
            data['last_name'] = organizer.organizer.last_name,
            data['last_name'] = str(data['last_name'][0])  
            data['organizer_id'] = organizer.organizer.pk

            following.append(data)

        return Response({
            "Success":"True",
            "message":"Successfully found following organziers",
            "data":following
        })

    # endpoint to fetch featured events
    @action(detail = False, methods = ['GET'])
    def getFeaturedEvents(self, request, format = None):

        checkFeaturedEvents = FeaturedEvent.objects.all().values_list('event')

        if not checkFeaturedEvents.exists():
            return Response({
                "success":False,
                "message":"No Featured Event",
                "data":[]
            })
            
        getFeaturedEvents = Event.objects.filter(pk__in = checkFeaturedEvents)
        
        return Response({
            "success":True,
            "message":"Successfully found featured events",
            "data":utils.eventFormatter(getFeaturedEvents)
        })
        
    @action(detail=False,methods=['GET'])
    def getReservedEvents(self,request,format=None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        reservations = Reservation.objects.filter(attendee = attendee)
        if not reservations.exists():
            return Response({
                "success":False,
                "message":"No user reserved events",
                "data":[]
            })

        reservedEvents = []
        for reservation in reservations:
            reservedEvent = {}
            reservedEvent['name'] = reservation.event.name
            reservedEvent['id'] = reservation.event.pk
            reservedEvent['startDate'] = reservation.event.startDate
            reservedEvent['endDate'] = reservation.event.endDate
            reservedEvents.append(reservedEvent)

        return Response({
            "success":True,
            "message":"Found the user's reserved events",
            "data":reservedEvents
        })

    @action(detail = False, methods=['GET'])
    def getBookedEvents(self,request,format = None):
        attendee = extractToken.checkAttendeeToken(request.headers)

        bookings = Booking.objects.filter(attendee = attendee,has_attended__in=[False])
        if not bookings.exists():
            return Response({
                "success": False,
                "message":"No user booked events"
            })

        bookedEvents = []
        for booking in bookings:

            bookedEvent = {}
            bookedEvent['booking_id'] = booking.id
            bookedEvent['name'] = booking.event.name
            bookedEvent['id'] = booking.event.pk
            bookedEvent['startDate'] = booking.event.startDate
            bookedEvent['endDate'] = booking.event.endDate
            bookedEvent['is_verified'] = booking.is_verified
            bookedEvents.append(bookedEvent)

        return Response({
            "success":True,
            "message":"Found the user's booked events.",
            "data":bookedEvents
        })

    @action(detail=False,methods=['POST'])
    def addInterest(self,request,format = None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        if 'interests' not in request.data.keys():
            raise ValueError("interests is a required field")

        if not isinstance(request.data['interests'],List):
            raise ValueError("interests must be an array")

        checkCategories = Category.objects.filter(id__in = request.data['interests'])
        if len(checkCategories) != len(request.data['interests']):
            raise ValueError("All entered interests must be valid")

        checkInterest = Interests.objects.filter(attendee = attendee)
        for category in checkCategories:
            if checkInterest[0] in category.attendee_interest.all():
                raise ValueError("Already added the category " + str(category.title) +" to interests")

        if not checkInterest.exists():

            createdInterest = Interests(
                attendee = attendee,
            )

            createdInterest.save()

            for category in checkCategories:
                category.attendee_interest.add(createdInterest)
        
        else:
            for category in checkCategories:
                category.attendee_interest.add(checkInterest[0])

        return Response({
            "success":True,
            "message":"Successfully added the interests"
        })
    
    @action(detail=False,methods=['GET'])
    def getInterests(self,request,format = None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        checkInterest = Interests.objects.filter(attendee = attendee)
        checkCategories = Category.objects.filter(attendee_interest = checkInterest[0])

        if not checkInterest.exists():
            return Response({
                "success":False,
                "data":[]
            })

        categoryInterests = []
        for category in checkCategories:
            singleCategoryInterest = {}
            singleCategoryInterest['id'] = category.id
            singleCategoryInterest['title'] = category.title

            categoryInterests.append(singleCategoryInterest)

        return Response({
            "success":True,
            "data":categoryInterests
        })
    
    @action(detail=False,methods=['GET'])
    def getRecommendedEvents(self,request,format = None):

        attendee = extractToken.checkAttendeeToken(request.headers)

        checkInterest = Interests.objects.filter(attendee = attendee)
        checkCategories = Category.objects.filter(attendee_interest = checkInterest[0])

        getFollowing = OrganizerFollowing.objects.filter(attendeeId = attendee.pk).values('organizer')
        getEventsByFollowingOrganizers = Event.objects.filter(createdBy__in = getFollowing,subCategory__category__in = checkCategories,endDate__gte = timezone.now(),isHidden__in = [False])
        recommendedEvents = utils.eventFormatter(getEventsByFollowingOrganizers)

        return Response({
            "success":True,
            "data" : recommendedEvents
        })
    
    @action(detail=False,methods=['GET'])
    def getEventsThisWeek(self,request,format = None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        one_week_ago = timezone.now() - timedelta(days=7)
        one_week_later = timezone.now() + timedelta(days=7)

        eventsThisWeek = Event.objects.filter(startDate__gte = one_week_ago,startDate__lte = one_week_later,endDate__gte = timezone.now(),isHidden__in = [False]).order_by('-startDate')

        return Response({
            "success":True,
            "data": utils.eventFormatter(eventsThisWeek)
        })
    
    @action(detail=False,methods=['GET'])
    def getEventsThisMonth(self,request,format = None):

        attendee = extractToken.checkAttendeeToken(request.headers)

        d_fmt = "{0:>02}.{1:>02}.{2}"
        date_from = datetime.strptime(
            d_fmt.format(1,datetime.now().month,datetime.now().year), '%d.%m.%Y'
        ).date()
        last_day_of_month = calendar.monthrange(datetime.now().year,datetime.now().month)[1]
        date_to = datetime.strptime(
            d_fmt.format(last_day_of_month,datetime.now().month,datetime.now().year), '%d.%m.%Y'
        ).date()

        eventsThisMonth = Event.objects.filter(startDate__gte = date_from,startDate__lt = date_to,endDate__gte = timezone.now(),isHidden__in = [False])

        return Response({
            "success":True,
            "data":utils.eventFormatter(eventsThisMonth)
        })
    
    @action(detail=False,methods=['GET'])
    def getWalletInfo(self,request,format = None):

        attendee = extractToken.checkAttendeeToken(request.headers)

        checkWallet = Wallet.objects.filter(attendee = attendee)
        
        if checkWallet.exists():
            return Response({
                "success":True,
                "coins":checkWallet[0].coin
            })
        else:
            Wallet.objects.create(
                    attendee = attendee,
                coin = 0
            )
            return Response({
                "success":True,
                "coins":0
            })
    
    @action(detail = False,methods=['PUT'])
    def completeProfile(self, request, format = None):

        attendee = extractToken.checkAttendeeToken(request.headers)
        
        if attendee.profile_completed == True:
            raise ValueError("Account has a complete profile.")

        if 'dateofbirth' not in request.data.keys() or 'email' not in request.data.keys():
            raise ValueError("Email and dateofbirth must be in the request.")

        attendee.email = request.data['email']
        attendee.dateofbirth = request.data['dateofbirth']
        attendee.profile_completed = True

        attendee.save()
        
        return Response({
            "success": True,
            "message":"Account details have been completed."
        })

    # confirm booking payment        
    @action(detail = True,methods = ['GET'])
    def confirmBookingPayment(self, request , format = None, pk = None):
        try: 
            booked = Booking.objects.get(pk=pk)
        except:     
            return Response({
                "success":False,
                "is_verified": False,
                "message": "Booking not found."
            })

        if booked == None:  
            return Response({
                "success":False,
                "is_verified": False,
                "message": "Booking not found."
            })
            
        booked_payment = BookingPayment.objects.filter(booking = booked).last()

        if booked_payment:
            if booked_payment.isVerified:     
                return Response({
                    "success":True,
                    "is_verified": True
                })

        return Response({
            "success":True,
            "is_verified":False
        })

