from  pympler import asizeof
from pyndn.encoding import WireFormat
from device import Device
from device_profile import DeviceProfile
from pyndn import Data
import sys
from hashlib import sha256
from hmac_helper import HmacHelper
import hmac
import resource
from pympler import asizeof
import base64
#import RPi.GPIO as GPIO
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto import Random
from pyndn import Name
from  random import SystemRandom
from time import time as timestamp
from pyndn.sha256_with_rsa_signature import Sha256WithRsaSignature
from pyndn.encoding import WireFormat
from pyndn.util import Blob
from pyndn.digest_sha256_signature import DigestSha256Signature
from pyndn.sha256_with_rsa_signature import Sha256WithRsaSignature
from pyndn import Data, KeyLocatorType, Interest, Name
from hashlib import sha256
from random import SystemRandom
from time import time as timestamp
import base64
import hmac

"""
PUBLIC_KEY = bytearray([
   0x30, 0x81, 0x9d, 0x30, 0x0d, 0x06, 0x09, 0x2a, 0x86, 0x48, 0x86, 0xf7, 0x0d, 0x01, 0x01,
0x01, 0x05, 0x00, 0x03, 0x81, 0x8b, 0x00, 0x30, 0x81, 0x87, 0x02, 0x81, 0x81, 0x00, 0x9e,
0x06, 0x3e, 0x47, 0x85, 0xb2, 0x34, 0x37, 0xaa, 0x85, 0x47, 0xac, 0x03, 0x24, 0x83, 0xb5,
0x9c, 0xa8, 0x05, 0x3a, 0x24, 0x1e, 0xeb, 0x89, 0x01, 0xbb, 0xe9, 0x9b, 0xb2, 0xc3, 0x22,
0xac, 0x68, 0xe3, 0xf0, 0x6c, 0x02, 0xce, 0x68, 0xa6, 0xc4, 0xd0, 0xa7, 0x06, 0x90, 0x9c,
0xaa, 0x1b, 0x08, 0x1d, 0x8b, 0x43, 0x9a, 0x33, 0x67, 0x44, 0x6d, 0x21, 0xa3, 0x1b, 0x88,
0x9a, 0x97, 0x5e, 0x59, 0xc4, 0x15, 0x0b, 0xd9, 0x2c, 0xbd, 0x51, 0x07, 0x61, 0x82, 0xad,
0xc1, 0xb8, 0xd7, 0xbf, 0x9b, 0xcf, 0x7d, 0x24, 0xc2, 0x63, 0xf3, 0x97, 0x17, 0xeb, 0xfe,
0x62, 0x25, 0xba, 0x5b, 0x4d, 0x8a, 0xc2, 0x7a, 0xbd, 0x43, 0x8a, 0x8f, 0xb8, 0xf2, 0xf1,
0xc5, 0x6a, 0x30, 0xd3, 0x50, 0x8c, 0xc8, 0x9a, 0xdf, 0xef, 0xed, 0x35, 0xe7, 0x7a, 0x62,
0xea, 0x76, 0x7c, 0xbb, 0x08, 0x26, 0xc7, 0x02, 0x01, 0x11
    ])

"""


def generate_RSA(bits=2048):
    '''
    Generate an RSA keypair with an exponent of 65537 in PEM format
    param: bits The key length in bits
    Return private key and public key
    '''
    from Crypto.PublicKey import RSA 
    new_key = RSA.generate(bits, e=65537) 
    public_key = new_key.publickey().exportKey("PEM") 
    private_key = new_key.exportKey("PEM") 
    return private_key, public_key
pkeys = []
for i in range(200):
    print i
    private_key , public_key = generate_RSA()
    pkeys.append(public_key)

#private_key = private_key.split("\n")[1:-1]
#public_key =public_key.split("\n")[1]

#print private_key 
#print type(public_key)
#print public_key
#print len(public_key)
#l = public_key.split("\n")
#for e in l:
#    print e
#for e in l:
#    print len(e)

"""
random_generator = Random.new().read
key = RSA.generate(1024, random_generator)
public_key = key.publickey()
print public_key
print asizeof.asized(public_key).format()
"""
for each in range(10,201,10):


    keys = {}
    #keys["/UA-cs-718/device/light/1/private-key"] = private_key

    for i in range(each):
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        public_key = key.publickey()
        key_name = "/UA-cs-718/device/switch/"+str(i)+"/key/0"
        private_key , public_key = generate_RSA()
        keys[key_name] = pkeys[i]



    print len(keys.keys())
    print asizeof.asized(keys).format()
