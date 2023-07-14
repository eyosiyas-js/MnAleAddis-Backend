from django.utils import timezone

from app.models import Story

def checkExpiredStories():
    checkStories = Story.objects.exclude(dateCreated__gte=timezone.now().replace(hour=0, minute=0, second=0),dateCreated__lte=timezone.now().replace(hour=23,minute=59,second=59)).delete()
