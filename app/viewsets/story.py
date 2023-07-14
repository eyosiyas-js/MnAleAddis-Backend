from django.utils.translation import override
from django.utils import timezone

from rest_framework import status,viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models import *
from app.serializers import * 
from app.scripts import extractToken,utils,checkOrganizerPlan,notifyAttendees,checkExpiredStories
from app.signals import signals
# from app.tasks import check_expired_stories

import imghdr
import cloudinary,cloudinary.uploader,cloudinary.api

class StoryViewSet(viewsets.ModelViewSet):

    queryset = Story.objects.all()
    serializer_class = StorySerializer

    def list(self,request,format = None):
        attendee = extractToken.checkAttendeeToken(request.headers)
        checkExpiredStories.checkExpiredStories()
        
        allStories = Story.objects.all()

        if len(allStories) == 0:
            return Response({
                "success":False,
                "data":utils.storyFormatter(allStories)
            })
        
        # check_expired_stories.delay()
        return Response({
            "success":True,
            "data":utils.storyFormatter(allStories)
        })


    def create(self,request,format = None):
        
        organizer = extractToken.checkOrganizerToken(request.headers)

        allowedVideoTypes = ['video/mp4','video/mkv','video/avi','video/mov']
        allowedImageTypes = ['png','jpeg','jpg']


        if 'title' not in request.data.keys():
            raise ValueError("All required fields must be input")
        if 'video' not in request.data.keys() and 'image' not in request.data.keys():
            raise ValueError("Either of the video or image property is required")

        if 'video' in request.data.keys():
            if 'image' in request.data.keys():
                raise ValueError("Either of image or video is allowed")
            
            
            video = request.FILES['video']
            
            if video.content_type not in allowedVideoTypes:
                raise ValueError("Video type not allowed")
            if video.size/ 1000000 > 20:
                raise ValueError("Video must be less than 20 mb")

            uploadedFile = cloudinary.uploader.upload(
                video,
                folder = "MinAleAddis/Organizer/Stories/",
                public_id = 'Story ' + str(organizer.pk) + request.data['title'],
                overwrite = True,
                resource_type = "video"
            )

            createdStory = Story.objects.create(
                title = request.data['title'],
                file_url = uploadedFile['url'],
                isVideo = True,
                isImage = False,
                createdBy = organizer
            )

            return Response({
                "success":True,
                "message":"Successfully created the story",
                "data":{
                    "id":createdStory.pk,
                    "file_url": createdStory.file_url,
                    "isVideo": createdStory.isVideo,
                    "isImage": createdStory.isImage,
                    "createdBy_id": createdStory.createdBy.id,
                    "dateCreated": str(createdStory.dateCreated)
                }
            })

        if 'image' in request.data.keys():
            if 'video' in request.data.keys():
                raise ValueError("Either of image or video is allowed")
            
            image = request.FILES['image']
            if imghdr.what(image) not in allowedImageTypes:
                raise ValueError("Video type not allowed")
            
            if image.size / 1000000 > 20:
                raise ValueError("Image must be less than 20 mb.")

            uploadedImage = cloudinary.uploader.upload(
                image,
                folder = "MinAleAddis/Organizer/Stories/",
                public_id = 'Story ' + str(organizer.pk) + request.data['title'] + str(timezone.now()),
                overwrite = True,
                resource_type = "image"
            )

            createdImageStory = Story.objects.create(
                title = request.data['title'],
                file_url = uploadedImage['url'],
                isVideo = False,
                isImage = True,
                createdBy = organizer
            )

            return Response({
                "success":True,
                "message":"Successfully created the story",
                "data":{
                    "id":createdImageStory.pk,
                    "file_url": createdImageStory.file_url,
                    "isVideo": createdImageStory.isVideo,
                    "isImage": createdImageStory.isImage,
                    "createdBy_id": createdImageStory.createdBy.id,
                    "dateCreated": str(createdImageStory.dateCreated)
                }
            })

