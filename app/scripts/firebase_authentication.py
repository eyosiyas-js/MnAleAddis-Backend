from tokenize import String
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
}

firebase = pyrebase.initialize_app(config)

# create user with phone and password

auth = firebase.auth()

def CreateUserInFirebase(email, password, phone) -> String:
    user = auth.create_user_with_email_and_password(email=email, password=password)
    # data = {'phone' : phone}
    # db = firebase.database()
    # db.child('users').push(data)
    print(user)
    return user['idToken']
