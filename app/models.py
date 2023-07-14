# from django.db import models
from email.policy import default
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.db.models.deletion import CASCADE
from django.utils.translation import gettext_lazy as _
from location_field.models.plain import PlainLocationField
from djongo import models
from django.core.validators import MaxValueValidator,MinValueValidator

from django.db.models import Func
# Create your models here.

NOTIFICATION_TYPE_CHOICES = (
    ('Event-Creation','Event-Creation'),
    ('Reminder','Reminder'),
    ('User-Following','User-Following'),
    ('Review-Reminder','Review-Reminder')
)

class Tag(models.Model):
    tag = models.CharField(max_length=30)
    isVirtual = models.BooleanField(default=False)

class Event(models.Model):
    name = models.CharField(max_length=150)
    normalPrice = models.FloatField()
    vipPrice = models.FloatField(default=0)
    vvipPrice = models.FloatField(default=0)
    description = models.CharField(max_length=250)
    startDate = models.DateTimeField()
    endDate = models.DateTimeField(blank=True)    
    venue = models.CharField(max_length=200,default="")
    subCategory = models.ForeignKey('SubCategory',on_delete=models.CASCADE,default="",related_name="subcategory")
    location = PlainLocationField(based_fields=['city'],zoom=7,default="")
    tags = models.JSONField()
    phones = models.JSONField()
    image_url = models.URLField(blank=True)
    createdBy = models.ForeignKey('ExtendedUser',on_delete=models.CASCADE,null=False,default="")
    dressingCode = models.CharField(max_length=150,default="")
    maxNoOfAttendees = models.IntegerField(default=100)
    noOfViews = models.IntegerField(default=0)
    isHidden = models.BooleanField(default=False)
    isVirtual = models.BooleanField(default=False)
    #private Event key
    prvt_evnt_key = models.CharField(max_length=20, null=True, blank=True)
    phone = models.CharField(blank=True,max_length=13)
    org_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True,max_length=255,verbose_name="email")
    isPrivate = models.BooleanField(default=False)
    isActive = models.BooleanField(default = True)

class GraduationEvent(models.Model):
    name = models.CharField(max_length=150)
    price = models.FloatField(default=0)
    description = models.CharField(max_length=250)
    startDate = models.DateTimeField()
    venue = models.CharField(max_length=200,default="")
    location = PlainLocationField(based_fields=['city'],zoom=7,default="")
    phones = models.JSONField()
    image_url = models.URLField(blank=True)
    createdBy = models.ForeignKey('ExtendedUser',on_delete=models.CASCADE,null=False,default="")
    maxNoOfAttendees = models.IntegerField(default=100)
    noOfViews = models.IntegerField(default=0)
    isHidden = models.BooleanField(default=False)
    eventkey = models.CharField(max_length=20)
    minPercentageToPay = models.FloatField()
    
    
class Category(models.Model):
    title = models.CharField(max_length=150)

class SubCategory(models.Model):
    title = models.CharField(max_length=150)
    category = models.ForeignKey(Category,on_delete=models.CASCADE)

class ExtendedUser(AbstractUser):

    SEX_CHOICES = (
        ('F','Female',),
        ('M','Male',)
    )

    phone = models.CharField(blank=False,max_length=13,)
    email = models.EmailField(blank=False,max_length=255,verbose_name="email")
    sex = models.CharField(max_length=1,choices=SEX_CHOICES)
    image_url = models.URLField(null=True)
    isOrganizer = models.BooleanField(default=False)
    likedEvents = models.ManyToManyField(Event,related_name='likedBy')
    isBlocked = models.BooleanField(default=False)
    links = models.JSONField(null=True,default=None)
    dateofbirth = models.DateTimeField(default="1999-03-12T01:12:00Z")
    # age = models.CharField(default=25,max_length=3)
    firebase_uuid = models.CharField(max_length = 100,null = True)
    profile_completed = models.BooleanField(default = True)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"

class OrganizerDetail(models.Model):
    organizer = models.OneToOneField(ExtendedUser,on_delete=models.CASCADE)
    kebele_image_url1 = models.URLField(null=True)
    payment_plan = models.ForeignKey('PaymentPlan',on_delete=models.CASCADE)
    isVerified = models.BooleanField(default=False)
    kebele_image_url2 = models.URLField(null=True)

class FeaturedEvent(models.Model):
    event = models.ForeignKey(Event,on_delete = models.CASCADE)
    timestamp = models.DateTimeField(auto_now = True)
    
class SavedEvent(models.Model):
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

class EventLike(models.Model):
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
class EventSeen(models.Model):
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)

class OrganizerFollowing(models.Model):
    
    attendeeId = models.IntegerField()
    organizer = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    createdAt = models.DateTimeField(auto_now=True)
class PaymentPlan(models.Model):
    id = models.AutoField(primary_key=True,unique=True)
    name = models.CharField(max_length=20,unique=True)
    price_per_month = models.PositiveIntegerField(validators=[
        MinValueValidator(1),
    ])
    percentage_cut = models.FloatField(validators=[
        MinValueValidator(1),
        MaxValueValidator(99)
    ])
    description = models.CharField(max_length=300)

class Reservation(models.Model):

    TYPE_CHOICES = (
        ('N','Normal',),
        ('V','Vip',),
        ('VV','VVip')
    )

    id = models.AutoField(primary_key=True,unique=True)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    # type = models.CharField(max_length=2,choices=TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now=True)
    number = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ]
    )
    pending_status = models.BooleanField(default=True)

class Booking(models.Model):

    TYPE_CHOICES = (
        ('N','Normal',),
        ('V','Vip',),
        ('VV','VVip')
    )

    id = models.AutoField(primary_key=True,unique=True)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    type = models.CharField(max_length=2,choices=TYPE_CHOICES)
    timestamp = models.DateTimeField(auto_now=True)
    number = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10)
        ]
    )
    code = models.CharField(max_length=20,unique=True)
    qrcode = models.URLField(null=True)
    has_attended = models.BooleanField(default=False)
    is_verified = models.BooleanField(default = True)
    discount_code = models.CharField(max_length=20, default='0')

class BookingPayment(models.Model):
    transactionNo = models.CharField(max_length = 100)
    booking = models.ForeignKey(Booking,on_delete = models.CASCADE)
    amount = models.IntegerField()
    timestamp = models.DateTimeField(auto_now = True)
    isVerified = models.BooleanField(default = False)

class GraduationBooking(models.Model):

    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    graduationEvent = models.ForeignKey(GraduationEvent,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now=True)
    percentagePayed = models.FloatField(default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    code = models.CharField(max_length=20,unique=True)
    qrcode = models.URLField(null=True)
    has_attended = models.BooleanField(default=False)
class Review(models.Model):

    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    rate = models.IntegerField(
        validators = [
            MinValueValidator(0),
            MaxValueValidator(5)
        ]
    )
    timestamp = models.DateTimeField(auto_now=True)
    comment = models.CharField(max_length=300)

class Usher(models.Model):

    name = models.CharField(max_length = 200)
    code = models.CharField(max_length = 7,unique = True)
    event = models.ForeignKey(Event,on_delete = models.CASCADE)
    timestamp = models.DateTimeField( auto_now=True)
class Referral(models.Model):

    user = models.ForeignKey(ExtendedUser,on_delete = models.CASCADE)
    event = models.ForeignKey(Event,on_delete = models.CASCADE) 
    createdAt = models.DateTimeField(auto_now=True)
    noOfUsersForReferral = models.IntegerField(default=0)
    code = models.CharField(max_length=10,default="NDzkGoTCdRcaRyt7GOepg")

class Notification(models.Model):

    title = models.CharField(max_length=500)
    event = models.ForeignKey(Event,on_delete = models.CASCADE,null=True)
    fromUser = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE,null=True,related_name='from_user')
    toUser = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE,related_name='to_user')
    type = models.CharField(choices=NOTIFICATION_TYPE_CHOICES,max_length=300)
    isSeen = models.BooleanField(default=False)
    dateCreated = models.DateTimeField( auto_now=True)

class Story(models.Model):

    title = models.CharField(max_length = 300)
    file_url = models.URLField()
    isVideo = models.BooleanField(default = False)
    isImage = models.BooleanField(default = False)
    createdBy = models.ForeignKey(ExtendedUser,on_delete = models.CASCADE)
    dateCreated = models.DateTimeField(auto_now = True)

class Group(models.Model):

    name = models.CharField(max_length=200)
    members = models.ManyToManyField(ExtendedUser)
    createdBy = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE,related_name="group_owner")
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    dateCreated = models.DateTimeField(auto_now = True)

class PromoCode(models.Model):

    code = models.CharField(max_length=20)
    event = models.ForeignKey(Event,on_delete=models.CASCADE)
    percentage_decrease = models.FloatField()
    usedBy = models.ManyToManyField(ExtendedUser)
    dateCreated = models.DateTimeField(auto_now=True)
    maxNoOfAttendees = models.IntegerField()

class Interests(models.Model):

    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    interests = models.ManyToManyField(Category,related_name="attendee_interest")
    timestamp = models.DateTimeField(auto_now=True)

class Survey(models.Model):

    title = models.CharField(max_length=200)
    organizer = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE,related_name="organizer_survey")
    timestamp = models.DateTimeField(auto_now=True)

class SurveyResponse(models.Model):

    response = models.CharField(max_length=1000)
    survey = models.ForeignKey(Survey,on_delete=models.CASCADE)
    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE,related_name="attendee_survey_response")
    timestamp = models.DateTimeField(auto_now=True)

class Wallet(models.Model):

    attendee = models.ForeignKey(ExtendedUser,on_delete=models.CASCADE)
    coin = models.FloatField(default = 0)
    lastUpdated = models.DateTimeField(auto_now = True)

class WalletConfig(models.Model):

    coinPerSurvey = models.FloatField()
    coinPerEvent = models.FloatField()
    coinToBirr = models.FloatField()

class EventAttendee(models.Model):
    event = models.ForeignKey(Event,on_delete = models.CASCADE)
    phone = models.CharField(blank=False,max_length=13,)
    name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=False,max_length=255,verbose_name="email")
    isSend = models.BooleanField(default=False)