import collections
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP,PKCS1_v1_5
import binascii,re,datetime,json,hashlib,datetime,base64,requests
from base64 import b64decode,b64encode 

from .utils import randomCodeGenerator

class Telebirr:

    url = 'https://app.ethiomobilemoney.et:2121/ammapi/payment/service-openup/toTradeWebPay'
    
    def __init__(self,price,item):
        
        self.app_id = '5088a4df5341416395dc5a357bb7c6bb'
        self.app_key = "e85ce4d09a9a448e8f2919d0954a5163"
        self.nonce = randomCodeGenerator(32)
        self.public_key = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAnmEndOdJp1Wr9xAvLnWYXYViDShp3OcQRU9WoXb/260Ae40Y29BZCKu+4LdTjfwEQMjywO/Qe3hgyf9wW9EL7fG0F81TIA0LGsiAGf29BJ932sk8/Zvu7AkeETP6x5e+NS6HAs11oe5LHT4Px4ErMvwmphRvBacFkZvIRmzupKVdxrPkUsnPa7s1CbHRaTQVENWRKRopUoYSqAhjyVyDqGKamJRoC9rPcL+I7FHmiKT3SuimGJnxPtxD1ZnLwwvhok2BOtQhQMrZzEK1pYtr7UV7PmqjXRU/5LFJYZNrczUsETE6pc+CiC+50ALK7TYcFbnasr6mh2OxDZC5QgzP5QIDAQAB"

        ussd = {
            "appId": self.app_id,
            "notifyUrl": "http://167.235.30.159:17003/telebirr-notify/",
            "outTradeNo": self.nonce,
            # "receiveName": receive_name,
            "returnUrl": "http://167.235.30.159:17003/Events/telebirrSuccess/",
            "shortCode": "500376",
            "subject": str(item),
            "timeoutExpress": "30",
            "totalAmount": str(price),
            "nonce": self.nonce,
            "timestamp": str(int(datetime.datetime.now().timestamp() * 1000))
        }

        self.ussd = self.__encrypt__ussd(ussd = ussd , public_key = self.public_key)
        self.sign = self.__sign(ussd = ussd, app_key = self.app_key)
    
    @staticmethod
    def __encrypt__ussd(ussd,public_key):
        public_key = re.sub("(.{64})", "\\1\n", public_key.replace("\n", ""), 0, re.DOTALL)
        public_key = '-----BEGIN CERTIFICATE-----\n{}\n-----END CERTIFICATE-----'.format(public_key)
        ussd_json = json.dumps(ussd)
        encrypt = Telebirr.encrypt(public_key = public_key, msg = ussd_json)

        return encrypt
    
    @staticmethod
    def encrypt(public_key,msg):
        rsa = RSA.importKey(public_key)
        cipher = PKCS1_v1_5.new(rsa)
        ciphertext = b''
        for i in range(0,len(msg) //117):
            ciphertext += cipher.encrypt(msg[i * 117:(i + 1) * 117].encode('utf8'))
        ciphertext += cipher.encrypt(msg[(len(msg) // 117) * 117:len(msg)].encode('utf8'))
        return base64.b64encode(ciphertext).decode('ascii')
    
    @staticmethod
    def __sign(ussd, app_key):

        ussd_for_string_a = ussd.copy()
        ussd_for_string_a["appKey"] = app_key
        ordered_items = collections.OrderedDict(sorted(ussd_for_string_a.items()))
        string_a = ''
        for key,value in ordered_items.items():
            if string_a == '':
                string_a = key + "=" + value
            else:
                string_a += '&' + key + '=' + value
        string_b = hashlib.sha256(str.encode(string_a)).hexdigest()
        return str(string_b).upper()

    
    def request_params(self):
        return {
            "appid": self.app_id,
            "sign": self.sign,
            "ussd": self.ussd
        }
    
    def send_request(self):
        response = requests.post(url = self.url, json = self.request_params())
        return json.loads(response.text)