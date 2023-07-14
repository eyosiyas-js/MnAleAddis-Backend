
from app.signals import signals

from django.dispatch import receiver
from app.models import ExtendedUser,Event,EventSeen,Notification

from app.scripts import notifyAttendees,notifyOrganizer

from app.scripts import addToWallet as addScript

@receiver(signals.add_eventViewers_count)
def addEventCount(sender,userId,eventId,**kwargs):
     
    event = Event.objects.get(pk=eventId)
    print("sender")
    if sender == "non-user-event":

        Event.objects.filter(pk=eventId).update(
            noOfViews = event.noOfViews + 1
        )
    elif sender == "user-event":
        if not EventSeen.objects.filter(attendee_id = userId).exists():
            EventSeen.objects.create(
                attendee_id = userId,
                event_id = eventId
            )
            Event.objects.filter(pk=eventId).update(
                noOfViews = event.noOfViews + 1
            )

@receiver(signals.notify_followers)
def notifyFollowers(sender,event,organizer,**kwargs):
    notifyAttendees.notifyFollowingAttendees(event,organizer)

@receiver(signals.notify_interested)
def notifyInterested(sender,event,organizer,**kwargs):
    notifyAttendees.notifyInterestedAttendees(event,organizer)
    
@receiver(signals.notify_organizer_following)
def notifyOrganizerFollowing(sender,attendee,organizer,**kwargs):
    notifyOrganizer.notifyAttendeeFollowing(attendee,organizer)

@receiver(signals.add_to_wallet)
def addToWallet(sender,attendee,action,**kwargs):
    addScript.addToWallet(attendee,action)