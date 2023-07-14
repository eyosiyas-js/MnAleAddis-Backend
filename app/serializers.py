from django.db.models import fields
from rest_framework import serializers
from .models import *

class UserSerialzier(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ExtendedUser
        fields = ('id','phone','email','sex','is_staff','isOrganizer','image_url','username','first_name','last_name','likedEvents','firebase_uuid','dateofbirth','profile_completed')

class ChangePasswordSerializer(serializers.Serializer):
    model = ExtendedUser
    
    """
    Serializer for password change endpoint.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
class TagSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Tag
        fields = ('url','id','tag')

class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ('url','id','name','normalPrice','vipPrice','phones','vvipPrice','description','startDate','endDate','location','venue','tags','image_url','createdBy','dressingCode','subCategory','maxNoOfAttendees','noOfViews','isHidden', 'prvt_evnt_key', 'email', 'phone', 'org_name', 'isPrivate', 'isActive')

class GraduationEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = GraduationEvent
        fields = ('url','id','name','price','description','startDate','venue','location','phones','image_url','createdBy','maxNoOfAttendees','noOfViews','isHidden','eventkey','minPercentageToPay')
class SavedEventSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = SavedEvent
        fields = ('url','id','event','attendee')

class EventSeenSerialzier(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = EventSeen
        fields = ('url','id','event','attendee')

class OrganizerFollowingSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = OrganizerFollowing
        fields = ('url','id','attendeeId','organizer')

class PaymentPlanSerialzier(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = PaymentPlan
        fields = ('url','id','name','price_per_month','percentage_cut','description')

class ReviewSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Review
        fields = ('url','id','event','attendee','rate','comment','timestamp')

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = '__all__'

class SubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCategory
        fields = ('id','title','category')
    
class StorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Story
        fields = ('url','id','title','file_url','isVideo','isImage','createdBy','dateCreated') 

class SurveySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Survey
        fields = ('url','id','title','organizer','timestamp')
    
class UsherSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usher
        fields = ('id','name','code','event','timestamp')
class EventAttendeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventAttendee
        fields = ('id','name','phone','event','email','isSend')

class BookingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Booking
        fields = '__all__'

class BookingPaymentSerializer(serializers.ModelSerializer):

    class Meta:
        model = BookingPayment
        fields = '__all__'

# class PromoCodeSerializer(serializers.HyperlinkedModelSerializer):

#     class Meta:
#         model = PromoCode
#         fields = ('url','id','code','event','percentage_decrease','usedBy','dateCreated')