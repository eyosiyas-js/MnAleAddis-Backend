from app.scripts import telebirr2
from urllib.parse import urlparse
from urllib.parse import parse_qs

def bookWithTelebirr(price, item):
    telebirrObj = telebirr2.Telebirr(price, item)
    checkoutUrl = telebirrObj.send_request()

    url = checkoutUrl['data']['toPayUrl']
    parsedUrl = urlparse(url, allow_fragments=False)
    transactionNo = parse_qs(parsedUrl.query)['transactionNo'][0]
    
    return (checkoutUrl,transactionNo)