from django.http.response import HttpResponseNotFound
from django.shortcuts import redirect, render

from django.http import HttpResponse,response
from django.views import View
from django.views.decorators.csrf import csrf_protect,csrf_exempt

import requests

from .models import Referral,BookingPayment,Booking


client_id = "ARAlutHIJtf9dttZKDfaMXrQJAG8P_RgcYU_l947QQciz6q5Vpk4K7r5hKJ-lbFnAm-3tEEhM3l8LkVs"
client_secret = "EEX12Ce66S8Lxx8QvsHJMBkurN9ew26-vY_ryDZ1HX4xTsjh0dHTJ-w3Odw_3H7nt_Xso6uM46DVQiV5"



# Create your views here.
def event_invitation_view(request,referral_code):

    checkReferralCode = Referral.objects.filter(code = referral_code)
    if not checkReferralCode.exists():
        return HttpResponseNotFound('<h1>Page was not found</h1>')
    else:
        no_of_users = checkReferralCode[0].noOfUsersForReferral
        checkReferralCode.update(
            noOfUsersForReferral = no_of_users + 1
        )

        return redirect('https://play.google.com')

@csrf_exempt 
def telebirr_notify(request):

    # declares the public key 
    # later to be changed
    public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnmEndOdJp1Wr9xAvLnWYXYViDShp3OcQRU9WoXb/260Ae40Y29BZCKu+4LdTjfwEQMjywO/Qe3hgyf9wW9EL7fG0F81TIA0LGsiAGf29BJ932sk8/Zvu7AkeETP6x5e+NS6HAs11oe5LHT4Px4ErMvwmphRvBacFkZvIRmzupKVdxrPkUsnPa7s1CbHRaTQVENWRKRopUoYSqAhjyVyDqGKamJRoC9rPcL+I7FHmiKT3SuimGJnxPtxD1ZnLwwvhok2BOtQhQMrZzEK1pYtr7UV7PmqjXRU/5LFJYZNrczUsETE6pc+CiC+50ALK7TYcFbnasr6mh2OxDZC5QgzP5QIDAQAB"
    
    # assembles the request body
    data = {
        "value":request.body,
        "pub_key":public_key
    }

    # sends the telebirr encrypted data to a decryptor
    req = requests.post('http://dev.api.decryptor.mnaleaddis.com/decrypt/',data = data)
    
    # reads the wanted properties from the telebirr package
    totalAmount = req.json()['totalAmount']
    transactionNo = req.json()['tradeNo']

    checkPayment = BookingPayment.objects.filter(
        transactionNo = transactionNo
    )

    if checkPayment.exists():
        if checkPayment[0].isVerified == False:
            checkBooking = Booking.objects.filter(
                pk = checkPayment[0].booking.pk
            )
            if float(checkPayment[0].amount) == float(totalAmount):

                checkBooking.update(
                    is_verified = True
                )
                checkPayment.update(
                    isVerified = True
                )
                print("Successfully verified the booking payment.")
        

    return HttpResponse('<p>Success</p>')