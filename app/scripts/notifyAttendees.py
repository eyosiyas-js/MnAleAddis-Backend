import asyncio
from app.models import OrganizerFollowing,ExtendedUser,Notification,Interests
from channels.layers import get_channel_layer

def notifyFollowingAttendees(event,organizer):
    checkFollowers = OrganizerFollowing.objects.filter(organizer_id = organizer.id)

    followers = ExtendedUser.objects.filter(id__in =[cf.attendeeId for cf in checkFollowers ])

    fullname = organizer.first_name + " " + organizer.last_name

    for follower in followers:
        createdNotification = Notification.objects.create(
            title = "Organizer " + str(fullname) + " has created an event " + event.name,
            event = event,
            toUser = follower,
            type = "Event-Creation"
        )
        sendNotificationToUser('Attendee',follower.id,createdNotification)

def sendNotificationToUser(type,userId,notification):

    channel_layer = get_channel_layer()
    if type == 'Attendee':
        roomName = 'Attendee_%s' % userId
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    singleNotification = {
        "id":notification.id,
        "title":notification.title,
        "event_name":notification.event.name,
        "event_id":notification.event.id,
        "toUser":notification.toUser.id,
        "type":notification.type,
        "isSeen":notification.isSeen,
        "date":str(notification.dateCreated)
    }
    
    result = loop.run_until_complete(channel_layer.group_send(
        roomName,{
            "type":"chat_message",
            "message":singleNotification
        }
    ))

def notifyInterestedAttendees(event,organizer):
    category = event.subCategory.category

    ## to check Interested users
    checkInterested = Interests.objects.filter(interests__in = [category.pk])

    interestedUsers = ExtendedUser.objects.filter(interests__in = checkInterested)

    for user in interestedUsers:
        createdNotification = Notification.objects.create(
            title = "Event has been created in your interests "+ str(category.title),
            event = event,
            toUser = user,
            type = "Event-Creation"
        )
        sendNotificationToUser('Attendee',user.id,createdNotification)
