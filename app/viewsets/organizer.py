# from crypt import methods
import re
from tabnanny import check
import requests
from typing import List
from datetime import datetime
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.db.models import Sum
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from app.models import *
from app.serializers import *
from app.scripts import extractToken,utils

import imghdr
import cloudinary,cloudinary.uploader,cloudinary.api



class OrganizerViewSet(viewsets.ModelViewSet):

    queryset = ExtendedUser.objects.filter(is_staff__in=[False],isOrganizer__in=[True])
    serializer_class = UserSerialzier


    def list(self,request,format = None):
        checkOrganizers = ExtendedUser.objects.filter(is_staff__in=[False],isOrganizer__in=[True])

        allOrgs = []
        for organizer in checkOrganizers:
            singleOrg = {}
            singleOrg['name'] = organizer.first_name + " " + organizer.last_name
            singleOrg['id'] = organizer.id
            singleOrg['image'] = organizer.image_url

            allOrgs.append(singleOrg)

        return Response({
            "success":True,
            "data":allOrgs
        })    
    
    @action(detail = True,methods=['GET'])
    def getDetails(self,request,pk = None,format = None):

        # attendee = extractToken.checkAttendeeToken(request.headers)

        checkOrganizer = ExtendedUser.objects.filter ( pk= pk)

        if not checkOrganizer.exists():
            raise ValueError("User does not exist")
        
        if (checkOrganizer[0].isOrganizer == False) or (checkOrganizer[0].is_staff == True):
            raise ValueError("Invalid input")
        
        checkOrganizerDetail = OrganizerDetail.objects.filter(organizer = checkOrganizer[0])
        if (not checkOrganizerDetail.exists()) or (not checkOrganizerDetail[0].isVerified):
            return Response({
                "success":False,
                "message":"Organizer is not verified.",
                "data": [],
            },status.HTTP_400_BAD_REQUEST)
        
        links = []
        if checkOrganizer[0].links:
            for link in checkOrganizer[0].links:
                links.append({
                    "link":link['link'],
                    "noOfViews":link['noOfViews']
                })
        
        return Response({
            "success":True,
            "data":{
                "first_name":checkOrganizer[0].first_name,
                "last_name":checkOrganizer[0].last_name,
                "username":checkOrganizer[0].username,
                "image":checkOrganizer[0].image_url,
                "phone":checkOrganizer[0].phone,
                "email":checkOrganizer[0].email,
                "isVerified":True,
                "links":links
            }
        })
        
    def create(self,request, format=None):

        if not 'phone' or not 'username' or not 'first_name' or not 'last_name' or not 'password' in request.data.keys():
            raise ValueError("All required fields must be input")
        
        email = None
        if 'email' in request.data.keys():
            email = request.data['email']
                
        try:
            createdUser = ExtendedUser.objects.create(
                phone= request.data['phone'],
                email = email,
                username = request.data['username'],
                first_name = request.data['first_name'],
                last_name = request.data['last_name'],
                isOrganizer = True,
                links = []
            )
        except:
            raise ValueError("Invalid Inputs")

        createdUser.set_password(request.data['password'])
        createdUser.save()
        refresh = RefreshToken.for_user(createdUser)
       

        userSerialzier = UserSerialzier(createdUser,many=False,context={'request': request})

        return Response({
            "success":True,
            "message":"Account created successfully,Input scanned kebele id to get verified",
            "user":userSerialzier.data,
            "token":{
                "refresh":str(refresh),
                "access":str(refresh.access_token)
            }
        })
    
    @action(detail=False,methods=['PUT'])
    def editPassword(self,request,format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        fields = ('oldPassword','newPassword')
        if not all(name in request.data.keys() for name in fields):
            raise ValueError("All required fields must be input")

        
        oldPassword = request.data['oldPassword']
        newPassword = request.data['newPassword']

        if oldPassword == newPassword:
            raise ValueError("Old and new passwords must be different")

        if len(newPassword) < 6:
            raise ValueError("Password length must be 6 or more characters")
        
        if not organizer.check_password(oldPassword):
            raise ValueError("Error in changing Password")
        
        organizer.set_password(newPassword)
        organizer.save()

        return Response({
            "success":True,
            "message":"Succesfully updated the password"
        })

    @action(detail=False,methods=['POST'])
    def uploadKebeleId(self,request,pk=None,format=None):
        
        organizer = extractToken.getUnverifiedOrganizer(request.headers)
        checkOrganizerDetail = OrganizerDetail.objects.filter(organizer=organizer)
        # checkOrganizer = ExtendedUser.objects.filter(pk =pk)
        # if not checkOrganizer.exists() or not checkOrganizer[0].isOrganizer:
        #     raise ValueError("Organizer does not exist with the id.")

        allowedTypes = ['png','jpg','jpeg', 'pdf']
        
        kebele1 = request.FILES['kebele1']
        kebele2 = request.FILES['kebele2']
        
        if imghdr.what(kebele1) not in allowedTypes:
            raise ValueError("Image must of png, jpg, jpeg or pdf types")
        if imghdr.what(kebele2) not in allowedTypes:
            raise ValueError("Image must be png, jpg, jpeg or pdf types")

        uploadedFile1 = cloudinary.uploader.upload(
            kebele1,
            folder = "MinAleAddis/Organizer/kebeleIds/",
            public_id = 'Organizer ' + str(organizer.pk)+' kebeleId1',
            overwrite = True,
            resource_type = "image"
        )

        uploadedFile2 = cloudinary.uploader.upload(
            kebele2,
            folder = "MinAleAddis/Organizer/kebeleIds/",
            public_id = 'Organizer ' + str(organizer.pk) +' kebeleId2',
            overwrite = True,
            resource_type = "image"
        )

        if checkOrganizerDetail.exists():
            checkOrganizerDetail.update(
                kebele_image_url1 = uploadedFile1['url'],
                kebele_image_url2 = uploadedFile2['url'],
            )
        else:
            OrganizerDetail.objects.create(
                organizer = organizer,
                kebele_image_url1 = uploadedFile1['url'],
                kebele_image_url2 = uploadedFile2['url'],               
            )

        return Response({
            "success":True,
            "message":"Successfully Uploaded."
        })

    @action(detail=False,methods=['GET'])
    def getProfile(self,request,format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        userProfile = ExtendedUser.objects.get(pk = organizer.pk)
        links = []
        # print(userProfile.links)
        kebeleId1 = ''
        kebeleId2 = ''
        paymentPlanId = 0
        paymentPlanName = ''
        isVerified = False

        checkOrganizerDetail = OrganizerDetail.objects.filter(organizer = organizer)

        if checkOrganizerDetail.exists():
            kebeleId1 = checkOrganizerDetail[0].kebele_image_url1
            kebeleId2 = checkOrganizerDetail[0].kebele_image_url2
            paymentPlanId = checkOrganizerDetail[0].payment_plan.id
            paymentPlanName = checkOrganizerDetail[0].payment_plan.name
            isVerified = checkOrganizerDetail[0].isVerified

        if userProfile.links:
            for link in userProfile.links:
                links.append(
                    {
                        "link":link['link'],
                        "noOfViews":link['noOfViews']
                    }
                )
        return Response({
            "success":True,
            "profile":{
                "id":userProfile.pk,
                "first_name":userProfile.first_name,
                "last_name":userProfile.last_name,
                "username":userProfile.username,
                "date_of_birth":userProfile.dateofbirth,
                "image":userProfile.image_url,
                "phone":userProfile.phone,
                "email":userProfile.email,
                "kebeleId1":kebeleId1,
                "kebeleId2":kebeleId2,
                "paymentPlanId":paymentPlanId,
                "paymentPlanName":paymentPlanName,
                "isVerified":isVerified,
                "links":links
            }
        })    

    @action(detail=False,methods=['PUT'])
    def addLinksToProfile(self,request,format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        validate = URLValidator()
        links = []
        if 'links' not in request.data.keys():
            raise ValueError("Links is required")

        if not isinstance(request.data['links'],List):
            raise ValueError("links must be an array")
        
        if not organizer.links:
            organizer.links = []
        else:
            for singleLink in organizer.links:
                links.append({
                    "link":singleLink['link'],
                    "noOfViews":singleLink['noOfViews']
                }) 
        for link in request.data['links']:
            try:
                validate(link)
                requests.get(link)
                links.append({
                    "link":link,
                    "noOfViews":0
                })
            except ValidationError:
                raise ValueError("All values must be links")

        
 
        getOrganizer = ExtendedUser.objects.filter(pk = organizer.pk)
        getOrganizer.update(
            links = links
        )
        return Response({
            "success":True
        })

    @action(detail=False,methods=['GET'])
    def getLinksViewCount(self,request,format=None):
      organizer = extractToken.checkOrganizerToken(request.headers)

      if not organizer.links:
          return Response({
              "success":False,
              "message":"No social media link added.",
              "count":0  
          })

      count = 0
      for link in organizer.links:
          count = link['noOfViews'] + count

      return Response({
          "success":True,
          "message":"Fetched social media link views.",
          "count":count
      })  

    @action(detail=True,methods=['GET'])
    def viewEvents(self,request,pk=None,format=None):
        
        user = extractToken.checkAdminOrOrganizer(request.headers)

        checkOrganizer = ExtendedUser.objects.filter(pk = pk)
        if not checkOrganizer.exists():
            raise ValueError("User does not exist")
        
        orgEvents = Event.objects.filter(createdBy = checkOrganizer[0])

        if not orgEvents.exists():
            return Response({
                "status":"False",
                "message":"No organizer created events",
                "data":[]
            })

        allEvents = []
        for event in orgEvents:
            singleEvent = {}
            singleEvent['id'] = event.pk
            singleEvent['name'] = event.name
            singleEvent['description'] = event.description
            singleEvent['startDate'] = event.startDate
            singleEvent['endDate'] = event.endDate
            singleEvent['venue'] = event.venue

            allEvents.append(singleEvent)

        return Response({
            "Success":True,
            "message":"Found user events",
            "data":allEvents
        })

    def update(self, request, pk=None):

        checkOrganizer = extractToken.checkOrganizerToken(request.headers)

        organizer = ExtendedUser.objects.filter(pk=pk)

        if not organizer.exists():
            raise ValueError("Organizer does not exist")
        
        if checkOrganizer.pk != organizer[0].pk:
            raise ValueError("Action not allowed")
        
        if not 'first_name' or not 'last_name' or not 'username' or not 'email' or not 'phone' in request.data.keys():
            raise ValueError("All required fields must be input")
        
        if not request.data['first_name'] or not request.data['last_name'] or not request.data['username'] or not request.data['email'] or not request.data['phone'] :
            raise ValueError("All required fields must be input")

        organizer.update(
            first_name = request.data['first_name'],
            last_name = request.data['last_name'],
            username = request.data['username'],
            email = request.data['email'],
            phone = request.data['phone']
        )

        return Response({
            "success":True,
            "message":"Succesfully updated the user",
            "user":{
                "first_name":organizer[0].first_name,
                "last_name":organizer[0].last_name,
                "username":organizer[0].username,
                "email":organizer[0].email,
                "phone":organizer[0].phone
            }
        })

    @action(detail=False,methods=['POST'])
    def signin(self,request,format=None):
        
    
        if 'username' in request.data.keys():
            if 'email' in request.data.keys():
                raise ValueError("Only username or email are required")

            if not 'password' in request.data.keys():
                raise ValueError("Password is required")

            user = ExtendedUser.objects.get(username = request.data['username'])
            if user.isBlocked:
                raise ValueError("Account is temporarily deactivated,contact admins")
            if not user.check_password(request.data['password']):
                raise ValueError("Invalid Credentials")

            if user == None or user.is_staff != False or user.isOrganizer != True:
                raise ValueError("Invalid credentials")
            
            refresh = RefreshToken.for_user(user)
        
            return Response({
                'refresh':str(refresh),
                'access':str(refresh.access_token)
            })
        
        if 'email' in request.data.keys():
            if 'username' in request.data.keys():
                raise ValueError("Only username or email are required")

            if not 'password' in request.data.keys():
                raise ValueError("Password is required")
            
            user = ExtendedUser.objects.get(email = request.data['email'])
            if user.isBlocked:
                raise ValueError("Account is temporarily deactivated,contact admins")

            if not user.check_password(request.data['password']):
                raise ValueError("Invalid Credentials")
            
            if user == None or user.is_staff != False or user.isOrganizer != True:
                raise ValueError("Invalid credentials")

            refresh = RefreshToken.for_user(user)
        
            return Response({
                'refresh':str(refresh),
                'access':str(refresh.access_token)
            })

    @action(detail=False,methods=['GET'])
    def getFollowers(self,request,format=None):


        organizer = extractToken.checkOrganizerToken(request.headers)

        checkFollowers = OrganizerFollowing.objects.filter(organizer = organizer)
        if not checkFollowers.exists():
            return Response({
                "Success":"False",
                "message":"No followers",
                "data":[]
            })
        
        followers= []
        for attendee in checkFollowers:
            data = {}
            
            follower = ExtendedUser.objects.get(pk = attendee.attendeeId)
            
            data['username'] = follower.username
            data['first_name'] = follower.first_name
            data['last_name'] = follower.last_name
            data['attendee_id'] = follower.pk

            followers.append(data)
        return Response({
            "Success":"True",
            "message":"Succesfully found followers",
            "data":followers
        })

    @action(detail=False,methods=['GET'])
    def getPaymentPlan(self,request,format=None):
        
        organizer = extractToken.checkOrganizerToken(request.headers)
        
        checkOrganizerPlan = OrganizerDetail.objects.filter(organizer = organizer)
        if not checkOrganizerPlan.exists():
            return Response({
                "status":False,
                "message":"No Payment Plan Selected",
                "data":[]
            })

        return Response({
            "status":True,
            "message":"Succesfully Fetched the Payment Plan",
            "data":{
                "name":checkOrganizerPlan[0].payment_plan.name,
                "id":checkOrganizerPlan[0].payment_plan.pk
            }
        })


    @action(detail=False,methods = ['GET'])
    def getFollowersByMonth(self,request,format = None):
        
        organizer = extractToken.checkOrganizerToken(request.headers)

        checkFollowers = OrganizerFollowing.objects.filter(organizer_id = organizer.id)
        print(checkFollowers[0].createdAt)

        return Response({
            "success":True,
            "data":utils.dataAnalyticsFormatter(checkFollowers,'createdAt')
        })
    
    @action(detail = False, methods =['GET'])
    def getMyEvents(self, request, format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        myEvents = Event.objects.filter(createdBy = organizer)

        liveEvents = myEvents.filter(endDate__gte = timezone.now())
        pastEvents = myEvents.filter(endDate__lt = timezone.now())
        return Response({
            "success":True,
            "data":{
                "past":utils.eventFormatter(pastEvents),
                "live":utils.eventFormatter(liveEvents),
            }
        })

        
    @action(detail=False,methods=['POST'])
    def uploadAnyId(self,request,pk=None,format=None):
        """
        Upload Any Id type(Kebele-ID or Passport-ID)
        """   

        allowedTypes = ['png','jpg','jpeg']
        
        page1 = request.FILES['page1']
        resource_type = "image"

        if page1.content_type == "application/pdf":
            resource_type1 = "pdf"
        else:
            resource_type1 = "image"

        if resource_type1 == "image" and imghdr.what(page1) not in allowedTypes:
            raise ValueError("Image must of png, jpg, jpeg or pdf types")
        
        if 'page2' in request.FILES.keys() and request.FILES['page2']:
            page2 = request.FILES['page2']
            if page2.content_type == "application/pdf":
                resource_type2 = "pdf"
            else:
                resource_type2 = "image"
            page2 = request.FILES['page2']
            if resource_type2 == "image" and imghdr.what(page2) not in allowedTypes:
                raise ValueError("Image must be png, jpg, jpeg or pdf types")

        organizer = extractToken.getUnverifiedOrganizerForId(request.headers)
        checkOrganizerDetail = OrganizerDetail.objects.filter(organizer=organizer)
        
        uploadedFile1 = cloudinary.uploader.upload(
            page1,
            folder = "MinAleAddis/Organizer/kebeleIds/",
            public_id = 'Organizer ' + str(organizer.pk)+' page1',
            overwrite = True,
            resource_type = resource_type1
        )

        if 'page2' in request.FILES.keys() and request.FILES['page2']:
            uploadedFile2 = cloudinary.uploader.upload(
                page2,
                folder = "MinAleAddis/Organizer/kebeleIds/",
                public_id = 'Organizer ' + str(organizer.pk) +' page2',
                overwrite = True,
                resource_type = resource_type2
            )

        if 'page2' in request.FILES.keys() and request.FILES['page2']:
            if checkOrganizerDetail.exists():
                checkOrganizerDetail.update(
                    kebele_image_url1 = uploadedFile1['url'],
                    kebele_image_url2 = uploadedFile2['url'],
                )
            else:
                OrganizerDetail.objects.create(
                    organizer = organizer,
                    kebele_image_url1 = uploadedFile1['url'],
                    kebele_image_url2 = uploadedFile2['url'],               
                )
        else:
            if checkOrganizerDetail.exists():
                checkOrganizerDetail.update(
                    kebele_image_url1 = uploadedFile1['url'],
                )
            else:
                OrganizerDetail.objects.create(
                    organizer = organizer,
                    kebele_image_url1 = uploadedFile1['url'],             
                )

        return Response({
            "success":True,
            "message":"Successfully Uploaded."
        })

    
        

        

        