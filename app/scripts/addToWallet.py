from app.models import Wallet,WalletConfig,ExtendedUser

def addToWallet(attendee,action):
    
    getWalletConfig = WalletConfig.objects.filter()

    
    if getWalletConfig.exists():
        checkWallet = Wallet.objects.filter(attendee = attendee)
        if not checkWallet.exists():
            if action == 'user-survey-response':
                coin = getWalletConfig[0].coinPerSurvey    
            if action == 'user-booking-success':
                coin = getWalletConfig[0].coinPerEvent
            Wallet.objects.create(
                    attendee = attendee,
                    coin = coin
                )
        else:
            coin = checkWallet[0].coin
            if action == 'user-survey-response':
                coin = coin + getWalletConfig[0].coinPerSurvey
            if action == 'user-booking-success':
                coin = coin + getWalletConfig[0].coinPerEvent
            checkWallet.update(
                coin = coin 
            )
