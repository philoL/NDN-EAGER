# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Teng Liang <philoliang2011@gmail.com>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU General Public License is in the file COPYING.

"""
This module gives an example of LED instance
"""
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
import RPi.GPIO as GPIO
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

def memory_usage():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


class LED(Device):

    def __init__(self,configFileName=None):
        super(LED, self).__init__(configFileName)

        self._identity = "/UA-cs-718/device/light/1"
        self._deviceProfile = DeviceProfile(category = "device", type_= "light", serialNumber = "1")
        self.addCommands(['turnOn','turnOff','status'])

        self.hmachelper = HmacHelper("default", None)

        random_generator = Random.new().read
        self.AS_key = RSA.generate(1024, random_generator)
        random_generator = Random.new().read
        self.key = RSA.generate(1024, random_generator)
        self.keys = {} 
        self.keyName = Name('/UA-cs-718/device/light/1/service/status/seed/0/device/switch/1/key/0')
        certificate_hash = SHA256.new(self.keyName.toUri()).digest()
        certificate = self.AS_key.sign(certificate_hash,"")

        self.keys[self.keyName.toUri()] = (self.key.publickey(),certificate)
        #generate interest
        self.random = SystemRandom()
        nonceValue = bytearray(8)
        for i in range(8):
            nonceValue[i] = self.random.randint(0,0xff)
        timestampValue = bytearray(8)
        ts = int(timestamp()*1000)
        for i in range(8):
            byte = ts & 0xff
            timestampValue[-(i+1)] = byte
            ts = ts >> 8

        wireFormat = WireFormat.getDefaultWireFormat()

        s = Sha256WithRsaSignature()
        s.getKeyLocator().setType(KeyLocatorType.KEYNAME)
        s.getKeyLocator().setKeyName(self.keyName)

        interest = Interest("/UA-cs-718/device/light/1/service/status")
        interestName = interest.getName()
        interestName.append(nonceValue).append(timestampValue)
        interestName.append(wireFormat.encodeSignatureInfo(s))
        interestName.append(Name.Component())
        encoding = interest.wireEncode(wireFormat).toSignedBuffer()
        self.h = SHA256.new(bytes(encoding)).digest()
        #hash = hmac.new(self.h, encoding, sha256).digest()
        signature = self.key.sign(self.h, "")
        s.setSignature(Blob(str(signature[0])))
        interest.setName(interestName.getPrefix(-1).append(
            wireFormat.encodeSignatureValue(s)))
    
        self.interest = interest

      
    @profile
    def status(self, interest, transport):
        signature = self.hmachelper.extractInterestSignature(self.interest) 
        signature_raw = signature.getSignature().toRawStr()
        rsa_signature = (long(signature_raw), )
        access_key_name = signature.getKeyLocator().getKeyName().toUri()
        encoding = bytes(self.interest.wireEncode(WireFormat.getDefaultWireFormat()).toSignedBuffer())
        # authentication 
        access_key, certificate = self.keys[access_key_name]
        name_hash = SHA256.new(access_key_name).digest()
        if self.AS_key.verify(name_hash, certificate):
            interest_hash = SHA256.new(encoding).digest()
            if access_key.verify(interest_hash, rsa_signature):
                #cmd excution
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(17,GPIO.OUT)
                state = GPIO.input(17)
                GPIO.cleanup()
                if (state):
                    content = "on"
                else:
                    content = "off"
                data = Data(interest.getName())
                data.setContent(content)
                encoding = bytes(data.wireEncode(WireFormat.getDefaultWireFormat()).toSignedBuffer())
                #data signing
                data_hash = SHA256.new(encoding).digest()
                data_signature = self.key.sign(data_hash,"")
         
                s = Sha256WithRsaSignature()
                s.getKeyLocator().setType(KeyLocatorType.KEYNAME)
                s.getKeyLocator().setKeyName(self.keyName)
                s.setSignature(Blob(str(data_signature[0])))
                data.setSignature(s)
                self.sendData(data, transport, sign=False)

    def turnOn(self, interest, transport):
        
        print("Command turnOn is excuted, the light is on.")
        dat = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
        
    
    def turnOff(self, interest, transport):
        
        
        data = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
    
        """
        print ("seed : ", base64.b64encode(self.seeds["status"][0]))
        print ("interest name : ", interest.getName())
        print ("signature raw : ", base64.b64encode(signature_raw))
        print ("access_key_name : ", access_key_name)
        print ("encoding : ",base64.b64encode(encoding.toRawStr()))
        print ("access_key: ",base64.b64encode(access_key))
        print ("valid: ",base64.b64encode(valid_hash))
        """
  

if __name__ == "__main__":
    led = LED()
    led.start()
