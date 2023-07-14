from urllib.error import HTTPError
import pyrebase

config = {
  "apiKey": "AIzaSyB9X0GXNNl5F-EDB5uaTZWNYmxXo1iG0ac",
  "authDomain": "mnaleaddis-ea4c3.firebaseapp.com",
  "projectId": "mnaleaddis-ea4c3",
  "storageBucket": "mnaleaddis-ea4c3.appspot.com",
  "databaseURL": "https://mnaleaddis-ea4c3-default-rtdb.europe-west1.firebasedatabase.app/",
  "messagingSenderId": "910416394416",
  "appId": "1:910416394416:web:38d0562e38724f939aa375",
  "measurementId": "G-SXLWT6VKYF"
};

#firebase authentication
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
# database = firebase.database()

def checkUserWithUUID(idToken):
    
    # try:
    #     loginUser = auth.sign_in_with_email_and_password(email,password)
    #     print(loginUser)
    # except:
    #     raise ValueError("Email address not found.")
    checkUser = auth.get_account_info(idToken)

    return checkUser['users'][0]['localId']