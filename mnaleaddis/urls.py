
# from django.conf.urls import include
from django.contrib import admin
from django.urls import path,include,re_path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
# from BACKEND.app.views import makePayments

import app.views as views

from app.viewsets.admin import AdminViewSet
from app.viewsets.organizer import OrganizerViewSet
from app.viewsets.attendee import AttendeeViewSet
from app.viewsets.tag import TagViewSet
from app.viewsets.event import EventViewSet
from app.viewsets.savedEvents import SavedEventsViewset
from app.viewsets.eventSeen import EventSeenViewSet
from app.viewsets.organizerFollowing import OrganizerFollowingViewSet
from app.viewsets.paymentPlan import PaymentPlanViewSet
from app.viewsets.reviews import ReviewViewSet
from app.viewsets.category import CategoryViewSet
from app.viewsets.story import StoryViewSet
from app.viewsets.survey import SurveyViewSet
from app.viewsets.graduationEvents import GraduationEventViewSet
from app.viewsets.usher import UsherViewset
# from app.viewsets.promoCode import PromoCodeViewset

from rest_framework import routers,permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from app.viewsets.views import getEventDetail

schema_view = get_schema_view(
    openapi.Info(
        title = "Minale Addis API",
        default_version = 'v1',
        description = "The api documentation for min ale addis backend",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License")
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


router = routers.DefaultRouter()
router.register(r'Admins',AdminViewSet)
router.register(r'Organizers',OrganizerViewSet)
router.register(r'Attendees',AttendeeViewSet)
router.register(r'Tags',TagViewSet)
router.register(r'Events',EventViewSet)
router.register(r'Categories',CategoryViewSet)
router.register(r'SavedEvents',SavedEventsViewset)
router.register(r'EventsSeen',EventSeenViewSet)
router.register(r'OrganizerFollowing',OrganizerFollowingViewSet),
router.register(r'PaymentPlans',PaymentPlanViewSet),
router.register(r'Reviews',ReviewViewSet),
router.register(r'Stories',StoryViewSet),
router.register(r'Surveys',SurveyViewSet)
router.register(r'GraduationEvents',GraduationEventViewSet)
router.register(r'Ushers',UsherViewset)
# router.register(r'PromoCodes',PromoCodeViewset)

urlpatterns = [
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('',include(router.urls)),
    path('api/token/',TokenObtainPairView.as_view()),
    path('api/token/refresh/',TokenRefreshView.as_view()),
    path('admin/', admin.site.urls),
    path('event-invite/<str:referral_code>',views.event_invitation_view),
    path('telebirr-notify/',views.telebirr_notify),
    path('accounts/', include('django.contrib.auth.urls')),
    path('get-event-detail/<str:pk>', getEventDetail),
    path('Events/<str:pk>', getEventDetail),
]