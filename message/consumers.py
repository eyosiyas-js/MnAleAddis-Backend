from time import time
import pytz
from datetime import datetime
from django.utils import timezone
from typing import IO
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync,sync_to_async

from app.models import ExtendedUser,Notification,Event,Booking,Review

class AttendeeConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):

        user_Id = self.scope['url_route']['kwargs']['user_id']
        
        self.room_group_name = 'Attendee_%s' % user_Id
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, code):
        pass

    async def receive_json(self, content, **kwargs):
        
        user_Id = self.scope['url_route']['kwargs']['user_id']
        roomName = 'Attendee_%s' % user_Id

        if content == "Check":
            
            await self.checkBookedEvents(user_Id)
            notifications = await self.checkNotifications(user_Id)
            print("Here to check the New Notifications")
            await self.channel_layer.group_send(
                roomName,{
                    'type':'chat_message',
                    'message':notifications
                }
            )
        
        elif content == "Booked-Events-Reminder":
            notifications = await self.checkBookedEventsForAttendee(user_Id)
            await self.channel_layer.group_send(
                roomName,{
                    'type':'chat_message',
                    'message':notifications
                }
            )

    @database_sync_to_async
    def checkBookedEvents(self,userId):
        user = ExtendedUser.objects.get(pk = userId)

        checkBookings = Booking.objects.filter(attendee_id = userId,has_attended = True)
        
        checkBookedEvents = Event.objects.filter(booking__in = checkBookings)

        checkReviews = Review.objects.filter(event__in = checkBookedEvents, attendee_id = userId)

        if len(checkBookedEvents) == len(checkReviews):
            pass

        unratedEvents = []
        for review in checkReviews:
            for event in checkBookedEvents:
                if event.pk != review.event.pk:
                    checkNotification = Notification.objects.filter(event = event,type = "Review-Reminder",toUser_id = userId)
                    if not checkNotification.exists():
                        Notification.objects.create(
                            title = 'You have attended the event '+ str(event.name)+ ' but have not reviewed it yet.',
                            event = event,
                            toUser = user,
                            type = 'Review-Reminder',    
                        )




        
    @database_sync_to_async
    def checkNotifications(self,userId):
        notifications = Notification.objects.filter(toUser = userId,isSeen = False)
        allNotifications = []
        for notification in notifications:
            allNotifications.append({
                "id":notification.id,
                "title":notification.title,
                "event_name":notification.event.name,
                "event_id":notification.event.id,
                "toUser":notification.toUser.id,
                "type":notification.type,
                "isSeen":notification.isSeen,
                "date":str(notification.dateCreated)
            })
        
        return allNotifications
    
    @database_sync_to_async
    def checkBookedEventsForAttendee(self,userId):

        checkBookings = Booking.objects.filter(attendee_id = userId, has_attended = False)
        attendee = ExtendedUser.objects.get(pk = userId)

        checkBookedEvents = Event.objects.filter(booking__in = checkBookings,startDate__gte=timezone.now())

        allNotifications = []

        for bookedEvent in checkBookedEvents:
            checkNotification = Notification.objects.filter(event = bookedEvent,type="Reminder",toUser_id = userId,dateCreated__gte=timezone.now().replace(hour=0, minute=0, second=0),dateCreated__lte=timezone.now().replace(hour=23,minute=59,second=59))
            if not checkNotification.exists():
                createdNotification = Notification.objects.create(
                    title = "The event " + str(bookedEvent.name) + " 's start Date is very near,go check it out.",
                    event = bookedEvent,
                    toUser = attendee,
                    type = "Reminder"
                )
                allNotifications.append({
                    "id":createdNotification.id,
                    "title":createdNotification.title,
                    "event_name":createdNotification.event.name,
                    "event_id":createdNotification.event.id,
                    "toUser":createdNotification.toUser.id,
                    "type":createdNotification.type,
                    "isSeen":createdNotification.isSeen,
                    "date":str(createdNotification.dateCreated)
            })
            
            else:
                for notification in checkNotification:
                    allNotifications.append({
                        "id":notification.id,
                        "title":notification.title,
                        "event_name":notification.event.name,
                        "event_id":notification.event.id,
                        "toUser":notification.toUser.id,
                        "type":notification.type,
                        "isSeen":notification.isSeen,
                        "date":str(notification.dateCreated)
                    })
            
        return allNotifications

        # notification = {
        #     "title":notification.title,
        #         "event_name":notification.event.name,
        #         "event_id":notification.event.id,
        #         "toUser":notification.toUser.id,
        #         "type":notification.type,
        #         "isSeen":notification.isSeen,
        #         "date":str(notification.dateCreated)
        # }


    async def chat_message(self,event):
        await self.send_json(event['message'])

class OrganizerConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        user_Id = self.scope['url_route']['kwargs']['user_id']
        
        self.room_group_name = 'Organizer_%s' % user_Id
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, code):
        pass

    async def receive_json(self, content, **kwargs):
        print("Hello message for organizer")
        
    async def chat_message(self,event):
        await self.send_json(event['message'])