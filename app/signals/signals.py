from django import dispatch

add_eventViewers_count = dispatch.Signal(providing_args=['userId','eventId'])
notify_followers = dispatch.Signal(providing_args=['event','organizer'])
notify_interested = dispatch.Signal(providing_args=['event','organizer'])
notify_organizer_following = dispatch.Signal(providing_args=['attendee','organizer'])
add_to_wallet = dispatch.Signal(providing_args=['attendee','action'])