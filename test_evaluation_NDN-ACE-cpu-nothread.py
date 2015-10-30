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
This module defines Device class, which contains core modules of end device, including device discovery protocol, syncronization protocol, and access control manager.
"""


import time
import json
from pyndn import Name, Face, Interest, Data
from pyndn.threadsafe_face import ThreadsafeFace
from pyndn import KeyLocator, KeyLocatorType
from base_node import BaseNode
from hmac_helper import HmacHelper 
from pyndn.security.security_exception import SecurityException
from pyndn.util import Blob
from device_profile import  DeviceProfile
from access_control_manager import AccessControlManager
from hmac_key import HMACKey
from hashlib import sha256
import hmac
import base64


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)


class Counter(object):
    def __init__(self):
        self._callbackCount = 0

    def onData(self, interest, data):
        self._callbackCount += 1
        print self._callbackCount 
        #dump("Got data packet with name", data.getName().toUri())
        # Use join to convert each byte to chr.
        #dump(data.getContent().toRawStr())

    def onTimeout(self, interest):
        #self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri())

def main():
    face = Face('localhost')

    counter = Counter()

    name = Name("/UA-cs-718/device/light/1/service/status")
    seed = sha256("status").digest()
    accessTokenName = Name('/UA-cs-718/device/light/1/service/status/seed/0/device/switch/1/key/0').toUri()
    accessTokenKey = hmac.new(seed, accessTokenName, sha256).digest()
    accessToken = HMACKey(0,0,accessTokenKey,accessTokenName)
    a = AccessControlManager()

    while (1):
        interest = Interest(name)
        interest.setInterestLifetimeMilliseconds(3000) 
       
        a.signInterestWithHMACKey(interest,accessToken)
    
        face.expressInterest(interest, counter.onData, counter.onTimeout)
        #print interest.toUri()
        face.processEvents()
        time.sleep(0.51)
   

    #while counter._callbackCount < 3:
    #    face.processEvents()
    #    # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
    #    time.sleep(0.01)

    face.shutdown()

main()
    






