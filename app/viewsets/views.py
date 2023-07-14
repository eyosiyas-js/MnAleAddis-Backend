from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer

from app.models import Event, PromoCode
from app.serializers import EventSerializer, PromoCodeSerializer

@api_view(('GET',))
def getEventDetail(request,pk):
    discount_code = request.GET.get('discount-code', None)

    event = None
    if pk.isdigit():
        event = Event.objects.filter(pk=pk).last()
        
    if event is None:
        event = Event.objects.filter(prvt_evnt_key=pk, isHidden=True).last()
        if event is not None:
            serialized_event = EventSerializer(event, context={'request': request})
            return JsonResponse({
                "success":True,
                "data": serialized_event.data
            })
        return JsonResponse({
            "success":False,
            "message": "Event not found."
        })

    serialized_event = EventSerializer(event, context={'request': request})

    if not discount_code == None:
        promo_code = PromoCode.objects.filter(code=discount_code, event=event).last()
        serialized_event['discount-code'] = PromoCodeSerializer(promo_code, many=False).data
        
    return JsonResponse({
        "success":True,
        "data": serialized_event.data
    })