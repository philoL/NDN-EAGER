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

def memory_usage():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


class LED(Device):

    def __init__(self,configFileName=None):
        super(LED, self).__init__(configFileName)

        self._identity = "/US-cs-718/device/light/1"
        self._deviceProfile = DeviceProfile(category = "device", type_= "light", serialNumber = "1")
        self.addCommands(['turnOn','turnOff','status'])

        self.hmachelper = HmacHelper("default", None)
        #self.seeds = {}
        #self.seeds["turnOn"] = [sha256("turnOn").digest(),0]
        #self.seeds["turnOff"] = [sha256("turnOff").digest(),0]
        #self.seeds["status"] = [sha256("status").digest(),0]


      

    def status(self, interest, transport):
       
        print "Memory usage at the beginning of authentication %d KB." % memory_usage()
        seeds = {}
        seeds["turnOn"] = [sha256("turnOn").digest(),0]
        seeds["turnOff"] = [sha256("turnOff").digest(),0]
        seeds["status"] = [sha256("status").digest(),0]

        print("\n Memory usage for seeds dictinary: %d Bytes" %  sys.getsizeof(seeds))

        #print("In status function")   
        signature = self.hmachelper.extractInterestSignature(interest)
        print(" Memory usage for signature: %d Bytes " % sys.getsizeof(signature))

       
        access_key_name = signature.getKeyLocator().getKeyName().toUri()
        print(" Memory usage for access_key_name: %d Bytes" % sys.getsizeof(access_key_name))
        #aknuri = access_key_name.toUri()
        #print(" access_key_name memory usage: %d\n" % sys.getsizeof(aknuri))

        
        access_key = hmac.new( seeds["status"][0] , access_key_name).digest()
        print(" Memory usage for access_key: %d Bytes"% sys.getsizeof(access_key))

        encoding = interest.wireEncode(WireFormat.getDefaultWireFormat())
        
        print(" Memory usage for interest encoding: %d Bytes" % sys.getsizeof(encoding)) 

        valid_hash = hmac.new(access_key, encoding.toSignedBuffer(), sha256).digest()

        print(" Memory usage for valid_hash: %d Bytes\n" % sys.getsizeof(valid_hash))
            
        if signature.getSignature().toRawStr() == valid_hash:
            print("Evaluation : verified")
        print "Memory usage at the end of authentication %d KB." % memory_usage()

        data = Data(interest.getName())
        data.setContent("on")
        self.sendData(data, transport, sign=False)
        print("msg sent back")
 
    def turnOn(self, interest, transport):
        
        print("Command turnOn is excuted, the light is on.")

        data = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
        
    
    def turnOff(self, interest, transport):
        
        
        data = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
    
  

if __name__ == "__main__":
    led = LED()
    led.start()
