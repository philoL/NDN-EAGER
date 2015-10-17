# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014-2015 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU Lesser General Public License is in the file COPYING.
import time
import base64
import json
from pyndn import Name, Face, Interest, Data
from pyndn.key_locator import KeyLocator, KeyLocatorType
from hmac_helper import HmacHelper 
from hmac_key import HMACKey
import hmac 
from hashlib import sha256
from device_profile import  DeviceProfile
import sys
from pyndn.security import KeyChain
from base_node import BaseNode
from pyndn.security import SecurityException
from pyndn.util import Blob
from device_user_access_manager import DeviceUserAccessManager
from access_control_manager import AccessControlManager
from pyndn.sha256_with_rsa_signature import Sha256WithRsaSignature
from pyndn.digest_sha256_signature import DigestSha256Signature

try:
    # Use builtin asyncio on Python 3.4+, or Tulip on Python 3.3
    import asyncio
except ImportError:
    # Use Trollius on Python <= 3.2
    import trollius as asyncio
from pyndn import Name
# We must explicitly import from threadsafe_face. The pyndn module doesn't
# automatically load it since asyncio is optional.
from pyndn.threadsafe_face import ThreadsafeFace

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Counter(object):
    """
    Counter counts the number of calls to the onData or onTimeout callbacks.
    Create a Counter to call loop.stop() after maxCallbackCount calls to
    onData or onTimeout.
    """
    def __init__(self, maxCallbackCount):
        self.loop = asyncio.get_event_loop()
        self.face = ThreadsafeFace(self.loop, "localhost")
        self._maxCallbackCount = maxCallbackCount
        self._callbackCount = 0
        self.start = 0
        self.end = 0
        self.s = 0
        self.name = Name("/UA-cs-718/device/light/1/service/status")
        self.seed = sha256("status").digest()
        self.accessTokenName = Name('/UA-cs-718/device/light/1/service/status/seed/0/device/switch/1/key/0').toUri()
        self.accessTokenKey = hmac.new(self.seed, self.accessTokenName, sha256).digest()
        self.accessToken = HMACKey(0,0,self.accessTokenKey,self.accessTokenName)
        
        self.a = AccessControlManager()
        self.i = 0

    def onData(self, interest, data):
        # Use join to convert each byte to chr.
        self.end = time.time()
        self.s += self.end - self.start
        print "acc RTT: ", self.s
        dump("Got data packet with name", data.getName().toUri()) 
        dump(data.getContent().toRawStr())
        self.i += 1
        if self.i >= 10:
            exit(0)

        interest = Interest(self.name)
        interest.setInterestLifetimeMilliseconds(3000)
        self.a.signInterestWithHMACKey(interest,self.accessToken)
        self.face.expressInterest(interest, self.onData, self.onTimeout)
        self.start = time.time()

    def onTimeout(self, interest): 
        dump("Time out for interest", interest.getName().toUri())
    def expressInterest(self):
        print "interest expressing"
        interest = Interest(self.name)
        dump(interest.getName().toUri())
        interest.setInterestLifetimeMilliseconds(3000)
        self.a.signInterestWithHMACKey(interest,self.accessToken)
        self.face.expressInterest(interest, self.onData, self.onTimeout)
        self.start = time.time()


def main():

    #loop = asyncio.get_event_loop()
    #face = ThreadsafeFace(loop, "localhost")
    #face = Face("localhost")
    # Counter will stop the ioService after callbacks for all expressInterest.
    counter = Counter( 3)
    counter.expressInterest()

    # Try to fetch anything.
    #dump("Express name ", interest.toUri())
    """
    for i in range(100):
       print i
       interest = Interest(name1)
       interest.setInterestLifetimeMilliseconds(3000)
       a.signInterestWithHMACKey(interest,accessToken)

       face.expressInterest(interest, counter.onData, counter.onTimeout)
       counter.start = time.time()
       time.sleep(2)
    print coutner.s
   
    couter.face.expressInterest(interest, counter.onData, counter.onTimeout)
    """
    while counter._callbackCount < 10000:
        counter.face.processEvents()
        #We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(1)

    counter.face.shutdown()
    
main()
