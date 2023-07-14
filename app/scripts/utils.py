from datetime import date,datetime

import string,random
from app.models import EventSeen

from app.models import OrganizerFollowing

def is_datetime(dt):

    try:
        dt.date()
        return True
    except:
        if isinstance(dt,date):
            return False
    return False

def randomCodeGenerator(n):
    return ''.join(random.choices(string.ascii_letters+string.digits,k=n))

def randomNumberGenerator(n):
    return ''.join(random.choices(string.digits, k = n))
    
def getAgeRange(users):
    data = {}
    data['-18'] = 0
    data['18-40'] = 0
    data['40-60'] = 0
    data['60-'] = 0

    for user in users:
        if int(user.age) < 18:
            data['-18'] = data['-18'] + 1
        if int(user.age) >= 18 and int(user.age) < 40:
            data['18-40'] = data['18-40'] + 1 
        if int(user.age) >=40 and int(user.age) < 60:
            data['40-60'] = data['40-60'] + 1
        if int(user.age) >= 60:
            data['60-'] = data['60-'] + 1
    return data
    
def followingByMonth(queryset):
    data = {}
    data['January'] = 0
    data['February'] = 0
    data['March'] = 0
    data['April'] = 0
    data['May'] = 0
    data['June'] = 0
    data['July'] = 0
    data['August'] = 0
    data['September'] = 0
    data['October'] = 0
    data['November'] = 0
    data['December'] = 0

    checkDates = queryset.values('createdAt')

    for i in checkDates:
        print(i.get('createdAt').strftime("%B"))
        for key in data.keys():
            if key == i.get('createdAt').strftime("%B"):
                data[key] = data[key] + 1
    
    return data

def eventViewByMonth(queryset):

    data = {}
    data['January'] = 0
    data['February'] = 0
    data['March'] = 0
    data['April'] = 0
    data['May'] = 0
    data['June'] = 0
    data['July'] = 0
    data['August'] = 0
    data['September'] = 0
    data['October'] = 0
    data['November'] = 0
    data['December'] = 0

    checkDates = queryset.values('timestamp')

    for i in checkDates:
        for key in data.keys():
            if key == i.get('timestamp').strftime("%B"):
                data[key] = data[key] + 1

    return data

def dataAnalyticsFormatter(queryset,property):
    data = {}
    data['January'] = 0
    data['February'] = 0
    data['March'] = 0
    data['April'] = 0
    data['May'] = 0
    data['June'] = 0
    data['July'] = 0
    data['August'] = 0
    data['September'] = 0
    data['October'] = 0
    data['November'] = 0
    data['December'] = 0

    checkDates = queryset.values(property)

    for i in checkDates:
        for key in data.keys():
            if key == i.get(property).strftime("%B"):
                data[key] = data[key] + 1

    return data

def eventLikeFormatter(eventLikes):

    data = {}
    data['January'] = 0
    data['February'] = 0
    data['March'] = 0
    data['April'] = 0
    data['May'] = 0
    data['June'] = 0
    data['July'] = 0
    data['August'] = 0
    data['September'] = 0
    data['October'] = 0
    data['November'] = 0
    data['December'] = 0

    checkDates = eventLikes.values('timestamp')

def storyFormatter(stories):
    
    allStories = []
    for story in stories:
        singleStory = {}
        singleStory['id'] = story.id
        singleStory['file_url'] = story.file_url
        singleStory['isVideo'] = story.isVideo
        singleStory['isImage'] = story.isImage
        singleStory['createdBy_id'] = story.createdBy.id
        singleStory['dateCreated'] = str(story.dateCreated)
        allStories.append(singleStory)
        
    return allStories

def graduationEventFormatter(Events):
    
    allEvents = []
    for event in Events:
        singleEvent = {}

        singleEvent['id'] = event.id
        singleEvent['name'] = event.name
        singleEvent['price'] = event.price
        singleEvent['description'] = event.description
        singleEvent['startDate'] = event.startDate
        singleEvent['venue'] = event.venue

        singleEvent['location'] = event.location
        singleEvent['phones'] = event.phones
        singleEvent['image_url'] = event.image_url

        singleEvent['createdBy'] = event.createdBy.id
        singleEvent['maxNoOfAttendees'] = event.maxNoOfAttendees
        singleEvent['noOfViews'] = event.noOfViews
        singleEvent['eventkey'] = event.eventkey
        singleEvent['minPercentageToPay'] = event.minPercentageToPay
        
        allEvents.append(singleEvent)
    
    return allEvents

def eventFormatter(Events):

    allEvents = []
    for event in Events:
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
        singleEvent['maxNoOfAttendees'] = event.maxNoOfAttendees
        singleEvent['isVirtual'] = event.isVirtual

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
        singleEvent['createdBy'] = event.createdBy.id
        singleEvent['dressingCode'] = event.dressingCode
        singleEvent['maxNoOfAttendees'] = event.maxNoOfAttendees
        singleEvent['noOfViews'] = event.noOfViews

        allEvents.append(singleEvent)
    
    return allEvents