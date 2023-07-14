from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from app.models import *
from app.serializers import *
from app.scripts import utils,extractToken
from app.signals import signals

class SurveyViewSet(viewsets.ModelViewSet):

    queryset = Survey.objects.all()
    serializer_class = SurveySerializer

    def create(self, request, *args, **kwargs):
        organizer = extractToken.checkOrganizerToken(request.headers)
        
        if 'title' not in request.data.keys():
            raise ValueError("Title is required")
        
        if not isinstance(request.data['title'],str):
            raise ValueError("title must be a string")
        if len(request.data['title']) < 20:
            raise ValueError("title must be greater than 20 characters")
        
        createdSurvey = Survey.objects.create(
            title = request.data['title'],
            organizer = organizer,
        )

        return Response({
            "success":True,
            "message":"Successfully created the survey",
            "data":{
                "title":createdSurvey.title,
                "timestamp":createdSurvey.timestamp
            }
        })

    def update(self, request, *args, **kwargs):
        organizer = extractToken.checkOrganizerToken(request.headers)

        id = kwargs['pk']

        checkSurvey = Survey.objects.filter(id = id)

        if organizer != checkSurvey[0].organizer:
            raise ValueError("Not allowed")
        

        if not checkSurvey.exists():
            raise ValueError("Survey does not exist.")
        
        if 'title' not in request.data.keys():
            raise ValueError("Title is required")
        
        if not isinstance(request.data['title'],str):
            raise ValueError("title must be a string")

        if len(request.data['title']) < 20:
            raise ValueError("title must be greater than 20 characters")

        updatedSurvey = checkSurvey.update(
            title = request.data['title']
        )

        return Response({
            "success":True,
            "message":"Successfully updated the survey details.",
            "data":{
                'id':checkSurvey[0].pk,
                'title':checkSurvey[0].title,
                'timestamp':checkSurvey[0].timestamp
            }
        })
    
    def destroy(self, request, *args, **kwargs):
        organizer = extractToken.checkOrganizerToken(request.headers)

        id = kwargs['pk']

        checkSurvey = Survey.objects.filter(id = id)
        if not checkSurvey.exists():
            raise ValueError("Survey does not exist.")

        if organizer != checkSurvey[0].organizer:
            raise ValueError("Not allowed")

        return super().destroy(request, *args, **kwargs)

    @action(detail=True,methods=['POST'])
    def respondToSurvey(self,request,pk = None,format = None):
        
        attendee = extractToken.checkAttendeeToken(request.headers)

        checkSurvey = Survey.objects.filter(pk = pk)
        if not checkSurvey.exists():
            raise ValueError("Survey does not exist.")

        if 'response' not in request.data.keys():
            raise ValueError("response is required")
        
        if not isinstance(request.data['response'],str):
            raise ValueError("title must be a string")

        checkResponse = SurveyResponse.objects.filter(attendee = attendee)
        if not checkResponse.exists():

            createdResponse = SurveyResponse.objects.create(
                response = request.data['response'],
                survey = checkSurvey[0],
                attendee = attendee
            )

            signals.add_to_wallet.send(sender="user-survey-response",attendee = attendee,action="user-survey-response")
            return Response({
                "success":True,
                "message":"Successfully created the response",
                "data":{
                    "id":createdResponse.id,
                    "response":createdResponse.response
                }
            })

        else:
            checkResponse.update(
                response = request.data['response']
            )
            
            return Response({
                "success":True,
                "message":"Successfully edited the response",
                "data":{
                    "id":checkResponse[0].id,
                    "response":checkResponse[0].response
                }
            })
            

    @action(detail=True,methods=['DELETE'])
    def deleteResponse(self,request,pk = None,format = None):

        attendee = extractToken.checkAttendeeToken(request.headers)
        
        checkSurveys = Survey.objects.filter(pk = pk)
        if not checkSurveys.exists():
            raise ValueError("Survey does not exist.")

        checkResponse = SurveyResponse.objects.filter(attendee = attendee,survey = checkSurveys[0])
        if not checkResponse.exists():
            raise ValueError("Response does not exist for the Survey")
        
        checkResponse.delete()

        return Response({
            "success":True,
            "message":"Successfully deleted the response for the survey."
        })
    
    @action(detail=True,methods=['GET'])
    def getResponsesForSurvey(self,request, pk = None,format = None):
        organizer = extractToken.checkOrganizerToken(request.headers)

        checkSurvey = Survey.objects.filter(organizer = organizer,pk = pk)

        if not checkSurvey.exists():
            raise ValueError("Does not exist")
        
        allResponses = []
        checkResponses = SurveyResponse.objects.filter(survey = checkSurvey[0])
        for response in checkResponses:
            singleResponse = {}
            singleResponse['id'] = response.id
            singleResponse['response'] = response.response
            singleResponse['attendee_id'] = response.attendee.id
            singleResponse['attendee_username'] = response.attendee.username
            singleResponse['timestamp'] = response.timestamp

            allResponses.append(singleResponse)

        return Response({
            "success":True,
            "data":allResponses
        })            
    @action(detail=False,methods=['GET'])
    def getMySurveys(self,request,format =None):

        organizer = extractToken.checkOrganizerToken(request.headers)

        checkSurveys = Survey.objects.filter(organizer = organizer)
        allSurveys = []
        
        if not checkSurveys.exists():
            return Response({
                "success":False,
                "message":"Found no surveys.",
                "data":[]
            })

        for survey in checkSurveys:
            singleSurvey = {}

            singleSurvey['id'] = survey.id
            singleSurvey['title'] = survey.title
            singleSurvey['timestamp'] = survey.timestamp

            allSurveys.append(singleSurvey)

        return Response({
            "success":True,
            "message":"Found surveys you created.",
            "data":allSurveys
        })