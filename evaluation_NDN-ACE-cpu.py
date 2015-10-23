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
from pyndn import Data, Interest, Name, KeyLocatorType
import sys
from hashlib import sha256
from hmac_helper import HmacHelper
import hmac
import resource
from pympler import asizeof
import base64
import RPi.GPIO as GPIO
from access_control_manager import AccessControlManager
from hmac_key import HMACKey
from pyndn.util import Blob

from pyndn.sha256_with_rsa_signature import Sha256WithRsaSignature




class LED(Device):

    def __init__(self,configFileName=None):
        super(LED, self).__init__(configFileName)

        self._identity = "/UA-cs-718/device/light/1"
        self._deviceProfile = DeviceProfile(category = "device", type_= "light", serialNumber = "1")
        self.addCommands(['turnOn','turnOff','status'])

        self.hmachelper = HmacHelper("default", None)
        self.seeds = {}
        self.seeds["turnOn"] = [sha256("turnOn").digest(),0]
        self.seeds["turnOff"] = [sha256("turnOff").digest(),0]
        self.seeds["status"] = [sha256("status").digest(),0]
        
        self.name = Name("/UA-cs-718/device/light/1/service/status")
        self.seed = sha256("status").digest()
        #self.accessTokenName = Name('/UA-cs-718/device/light/1/service/status/seed/0/device/switch/1/key/0').toUri()
        #self.accessTokenKey = hmac.new(self.seed, self.accessTokenName, sha256).digest()
        #self.accessToken = HMACKey(0,0,self.accessTokenKey,self.accessTokenName)


        #self.accessControlManager = AccessControlManager()
      
    #@profile
    def status(self, interest, transport):
        #print("in status")
        # parsing interests
        signature = self.hmachelper.extractInterestSignature(interest) 
        signature_raw = signature.getSignature().toRawStr()
        access_key_name = signature.getKeyLocator().getKeyName().toUri()
        encoding = interest.wireEncode(WireFormat.getDefaultWireFormat()) 
       

        # authentication
        access_key = hmac.new( self.seeds["status"][0] , access_key_name, sha256).digest()
        valid_hash = hmac.new(access_key, encoding.toSignedBuffer(), sha256).digest()
        
        if signature_raw == valid_hash:
            #print ("verified") 
            #cmd excution
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(17,GPIO.OUT)
            state = GPIO.input(17)
            GPIO.cleanup()
            if (state):
                content = "on"
            else:
                content = "off"
            
            #data generation
            data = Data(interest.getName())
            data.setContent(content)

            #self.accessControlManager.signDataWithHMACKey(data,self.accessToken)
            data_signature = Sha256WithRsaSignature()
            data_signature.getKeyLocator().setType(KeyLocatorType.KEYNAME)
            data_signature.getKeyLocator().setKeyName(access_key_name)
            wireFormat = WireFormat.getDefaultWireFormat()
            encoded = data.wireEncode(wireFormat).toSignedBuffer()
            
            s = hmac.new(access_key, encoded, sha256).digest()
            
            data_signature.setSignature(Blob(s))
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
