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
from  pympler import asizeof

def memory_usage():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


class LED(Device):

    def __init__(self,configFileName=None):
        super(LED, self).__init__(configFileName)

        self._identity = "/UA-cs-718/device/light/1"
        self._deviceProfile = DeviceProfile(category = "device", type_= "light", serialNumber = "1")
        self.addCommands(['turnOn','turnOff','status'])

        self.hmachelper = HmacHelper("default", None)
        self.keys = {}
        for i in range(50):
            key_name = "/UA-cs-718/device/switch/"+str(i)+"/key/0"
            self.keys[key_name] = sha256(key_name).digest()
 
    @profile
    def status(self, interest, transport):
       
        #authentication
        signature = self.hmachelper.extractInterestSignature(interest)
        access_key_name = signature.getKeyLocator().getKeyName().toUri()
        access_key = self.keys[access_key_name]
        encoding = interest.wireEncode(WireFormat.getDefaultWireFormat()) 
        valid_hash = hmac.new(access_key, encoding.toSignedBuffer(), sha256).digest()

        if signature.getSignature().toRawStr() == valid_hash:
            print("Evaluation : verified")
        #print "End - Memory usage : %d KB" % memory_usage()

        #data = Data(interest.getName())
        #data.setContent("on")
        #self.sendData(data, transport, sign=False)
        #print("msg sent back")

 
    def turnOn(self, interest, transport):
        
        print("Command turnOn is excuted, the light is on.")

        #data = Data(interest.getName())
        #data.setContent("success")
        #self.sendData(data, transport, sign=False)
        #print("msg success sent back")
        
    
    def turnOff(self, interest, transport):
        
        
        data = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
    
  

if __name__ == "__main__":
    led = LED()
    led.start()
