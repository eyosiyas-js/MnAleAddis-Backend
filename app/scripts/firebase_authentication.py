from tokenize import String
import pyrebase
import requests
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

def sign_in_user(email, password):
    try:
        user = auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        error_message = str(e)
        print("Error occurred during sign-in:", error_message)
        return None

def reset_password(email):
    try:
        auth.send_password_reset_email(email)
        print("Password reset email sent to:", email)
    except Exception as e:
        error_message = str(e)
        print("Error occurred during password reset:", error_message)

def confirm_password_reset(reset_code, new_password):
    try:
        auth = firebase.auth()
        reset_url = f"https://www.googleapis.com/identitytoolkit/v3/relyingparty/resetPassword?key={auth.api_key}"
        request_body = {
            "oobCode": reset_code,
            "newPassword": new_password,
        }
        response = requests.post(reset_url, json=request_body)
        
        if response.status_code == 200:
            response_data = response.json()
            user_email = response_data.get('email', '')
            print(user_email)

            print("Password reset confirmed successfully.")
            return  user_email
        else:
            print("Error occurred during password reset confirmation:", response.json())
    except Exception as e:
        error_message = str(e)
        print("Error occurred during password reset confirmation:", error_message) 
