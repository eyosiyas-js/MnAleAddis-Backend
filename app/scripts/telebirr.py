from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP,PKCS1_v1_5
import binascii,re,datetime,json,hashlib,datetime
from base64 import b64decode,b64encode 

from .utils import randomCodeGenerator

nonce = randomCodeGenerator(20)

appKey = "e8c20e9b5fed47bb89704959d2fb1c79"
publicKey = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAyZfgGYlKUi8e7gBAggLjLmw6ZFkmqntU/zB+VoZjxOBs5gL+GAgCNAJ+gL6ZH05qEhJPjKDS7j8ygknnMtLR71r0S5joLoTxDmXUYkRLF7BlzGybQcyISvK1u3YLI7QaGsw9xS2NCc3FUoqUERHoSPsxAlDeneBkj9tYzrrCUPMrTuSdUmD5qA647P9IuxhTIlb7036b5IBnhlQ5egCc+TaKEB6bHPQ52djJOsJCVn1uOpnCo9pKCzFDe3QYTI8OVDhFReTt5vCI0u9OlELzI1mYp/wS5ea0Uh2GaCWe92GKN770EJyajePBSZWLwjYlPsfI/qQ1wy+SV+Xof/HO2wIDAQAB"

signObj = {}
signObj['appId'] = "cef0e4e1ba6c4ab9ad9367d176816e2b"
signObj['nonce'] = nonce
# signObj['notifyUrl'] = ""
signObj['outTradeNo'] = "0533111222S001114129Umoja"
# signObj['receiveName'] = "Umoja Technologies PLC"
signObj['returnUrl'] = "https://mmpay.trade.pay/T0533111222S001114129"
signObj['shortCode'] = "220156"
signObj['subject'] = "WiFi"
signObj['timeoutExpress'] = "30"
signObj['timestamp'] = str(int(datetime.datetime.now().timestamp() * 1000))
signObj['totalAmount'] = "10"
signObj['appKey'] = appKey

def jsonSort(jsonObj):
    arr = []

    for key in jsonObj.keys():
        arr.append(key)

    arr.sort()

    str = ''
    for val in arr:
        str = str + val + "=" + jsonObj[val] + "&"

    return str[0:len(str)-1]

def SHA256(string):

    encoded = string.encode()
    result = hashlib.sha256(encoded)
    return result.hexdigest()

def getUSSDJson():

    dataObj = {}
    dataObj['appId'] = "cef0e4e1ba6c4ab9ad9367d176816e2b"
    dataObj['nonce'] = nonce
    dataObj['notifyUrl'] = ""
    dataObj['outTradeNo'] = "0533111222S001114129Umoja"
    dataObj['receiveName'] = "Umoja Technologies PLC"
    dataObj['returnUrl'] = "https://mmpay.trade.pay/T0533111222S001114129"
    dataObj['shortCode'] = "220156"
    dataObj['subject'] = "WiFI"
    dataObj['timeoutExpress'] = "30"
    dataObj['timestamp'] = str(int(datetime.datetime.now().timestamp() * 1000))
    dataObj['totalAmount'] = "10"
    # dataObj['appKey'] = appKey

    ussdJson = json.dumps(dataObj)

    return ussdJson

def encrypt(publicKey,message):
    publicKey = re.sub("(.{64})", "\\1\n", publicKey.replace("\n", ""), 0, re.DOTALL)
    publicKey = '-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----'.format(publicKey)
    rsa = RSA.importKey(publicKey)
    cipher = PKCS1_v1_5.new(rsa)
    ciphertext = b''
    for i in range(0, len(message) // 117):
        ciphertext += cipher.encrypt(message[i * 117:(i + 1) * 117].encode('utf8'))
    ciphertext += cipher.encrypt(message[(len(message) // 117) * 117: len(message)].encode('utf8'))
    return b64encode(ciphertext).decode('ascii')

def getRequestData():

    StringA = jsonSort(signObj)
    print(StringA)

    StringB = SHA256(StringA)
    sign = StringB.upper()
    ussdJson = getUSSDJson()
    ussd = encrypt(publicKey,ussdJson)

    body = {
        "appid":signObj['appId'],
        "sign":sign,
        "ussd":ussd
    }

    return body

