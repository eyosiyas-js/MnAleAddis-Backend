from django.utils.translation import deactivate
import jwt
from datetime import datetime
from app.models import ExtendedUser,OrganizerDetail

# def checkToken(headers):

def checkAdminToken(headers):
    
    if('Authorization' not in headers): raise ValueError("Authorization token is required")
    jwtToken = headers['Authorization']
    return getAdminFromToken(jwtToken)

def checkAdminOrOrganizer(headers):
    if('Authorization' not in headers): raise ValueError("Authorization token is required")
    jwtToken = headers['Authorization']
    return getAdminOrOrganizerFromToken(jwtToken)

def getUnverifiedOrganizer(headers):
    if('Authorization' not in headers): raise ValueError("Authorization token is required")
    jwtToken = headers['Authorization']
    return getUnverifiedOrganizerFromToken(jwtToken)

def getUnverifiedOrganizerForId(headers):
    if('Authorization' not in headers): raise ValueError("Authorization token is required")
    jwtToken = headers['Authorization']
    return getUnverifiedOrganizerFromTokenForId(jwtToken)

def getUnverifiedOrganizerFromTokenForId(token):
    index = token.find(' ')
    token = token[index:]

    decodedToken = jwt.decode(token, options={"verify_signature": False},algorithms=["HS256"])
    
    if decodedToken['token_type'] != 'access': raise ValueError("Invalid token")
    if datetime.now() > datetime.fromtimestamp(decodedToken['exp']):
        raise ValueError("Token has expired")

    organizer = ExtendedUser.objects.get(pk = decodedToken['user_id'])
    if organizer.is_staff or organizer.isOrganizer == False:
        raise ValueError("Token not for organizer")

    checkDetail = OrganizerDetail.objects.filter(organizer = organizer)

    return organizer

def getUnverifiedOrganizerFromToken(token):
    index = token.find(' ')
    token = token[index:]

    decodedToken = jwt.decode(token, options={"verify_signature": False},algorithms=["HS256"])
    
    if decodedToken['token_type'] != 'access': raise ValueError("Invalid token")
    if datetime.now() > datetime.fromtimestamp(decodedToken['exp']):
        raise ValueError("Token has expired")

    organizer = ExtendedUser.objects.get(pk = decodedToken['user_id'])
    if organizer.is_staff or organizer.isOrganizer == False:
        raise ValueError("Token not for organizer")

    checkDetail = OrganizerDetail.objects.filter(organizer = organizer)

    if checkDetail.exists() and checkDetail[0].isVerified == True:
       raise ValueError("Account not verified")

    return organizer

def getAdminOrOrganizerFromToken(token):
    index = token.find(' ')
    token = token[index:]

    decodedToken = jwt.decode(token, options={"verify_signature": False},algorithms=["HS256"])

    if decodedToken['token_type'] != 'access': raise ValueError("Invalid token")
    if datetime.now() > datetime.fromtimestamp(decodedToken['exp']):
        raise ValueError("Token has expired")
    
    user = ExtendedUser.objects.get(pk = decodedToken['user_id']) 
    if not user.is_staff and user.isOrganizer != True:
        raise ValueError("User not an admin or organizer")
    
    return user

def getAdminFromToken(token):
    
    index = token.find(' ')
    token = token[index:]

    decodedToken = jwt.decode(token, options={"verify_signature": False},algorithms=["HS256"])
    
    if decodedToken['token_type'] != 'access': raise ValueError("Invalid token")
    
    if datetime.now() > datetime.fromtimestamp(decodedToken['exp']):
        raise ValueError("Token has expired")

    admin = ExtendedUser.objects.get(pk = decodedToken['user_id']) 
    if not admin.is_staff or admin.isOrganizer == True:
        raise ValueError("Token not for admin")

    return admin

def checkAttendeeToken(headers):
    if('Authorization' not in headers): raise ValueError("Authorization token is required")
    jwtToken = headers['Authorization']
    return getAttendeeFromToken(jwtToken)

def getAttendeeFromToken(token):
    index = token.find(' ')
    token = token[index:]

    decodedToken = jwt.decode(token, options={"verify_signature": False},algorithms=["HS256"])
    
    if decodedToken['token_type'] != 'access': raise ValueError("Invalid token")
    if datetime.now() > datetime.fromtimestamp(decodedToken['exp']):
        raise ValueError("Token has expired")

    attendee = ExtendedUser.objects.get(pk = decodedToken['user_id']) 
    if attendee.is_staff or attendee.isOrganizer == True:
        raise ValueError("Token not for Attendee")

    return attendee

def checkOrganizerToken(headers):
    if('Authorization' not in headers): raise ValueError("Authorization token is required")
    jwtToken = headers['Authorization']
    return getOrganizerFromToken(jwtToken)

def getOrganizerFromToken(token):

    index = token.find(' ')
    token = token[index:]

    decodedToken = jwt.decode(token, options={"verify_signature": False},algorithms=["HS256"])
    
    if decodedToken['token_type'] != 'access': raise ValueError("Invalid token")
    
    if datetime.now() > datetime.fromtimestamp(decodedToken['exp']):
        raise ValueError("Token has expired")

    organizer = ExtendedUser.objects.get(pk = decodedToken['user_id'])

    if organizer.is_staff or organizer.isOrganizer != True:
        raise ValueError("Token not for Organizer")

    checkDetail = OrganizerDetail.objects.filter(organizer = organizer)
    if not checkDetail.exists() or (checkDetail[0].kebele_image_url1 == None and checkDetail[0].kebele_image_url2 == None):
        raise ValueError("Account not verified")

    if organizer.is_staff or organizer.isOrganizer == False:
        raise ValueError("Token not for organizer")

    return organizer