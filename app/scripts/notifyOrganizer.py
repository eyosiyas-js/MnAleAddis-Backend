import asyncio
from app.models import Notification
from channels.layers import get_channel_layer

def notifyAttendeeFollowing(attendee,organizer):
    fullname = attendee.first_name + " " + attendee.last_name
    createdNotification = Notification.objects.create(
        title = "You have been followed by " + str(fullname),
        toUser = organizer,
        fromUser = attendee,
        type = "User-Following"
    )

    sendNotificationToUser('Organizer',organizer.id,createdNotification)


def sendNotificationToUser(type,userId,notification):
    channel_layer = get_channel_layer()
    
    if type == 'Organizer':
        roomName = 'Organizer_%s' % userId
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    fullname = notification.fromUser.first_name + " " + notification.fromUser.last_name
    singleNotification = {
        "id":notification.id,
        "title":notification.title,
        "follower_name":fullname,
        "follower_id":notification.fromUser.id,
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