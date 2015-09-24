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
from pyndn.meta_info import MetaInfo


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
    def __init__(self, loop, maxCallbackCount):
        self._loop = loop
        self._maxCallbackCount = maxCallbackCount
        self._callbackCount = 0

    def onData(self, interest, data):
        dump("Got data packet with name", data.getName().toUri())
        # Use join to convert each byte to chr.
        dump(data.getContent().toRawStr())
        print(data.getMetaInfo().getFinalBlockId().getValue().toRawStr())
        self._callbackCount += 1
        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()

    def onTimeout(self, interest):
        dump("Time out for interest", interest.getName().toUri())

        self._callbackCount += 1
        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()

def main():
    seg = 0
    if len(sys.argv) < 3:
        print("argv error: please input capture or capture with #seg")
        exit(1)
    elif len(sys.argv) == 2:
        cmd = sys.argv[1]
    else:
        cmd = sys.argv[1]
        seg = sys.argv[2]

    loop = asyncio.get_event_loop()
    #face = ThreadsafeFace(loop, "localhost")
    face = Face("localhost")
    # Counter will stop the ioService after callbacks for all expressInterest.
    counter = Counter(loop, 3)

    seed = HMACKey(0,0,"seed","seedName")

    # Try to fetch anything.
    import time
    r = time.time()

    name1 = Name("/home/security/camera/0/"+cmd)
    name1.appendTimestamp(int(r))
    name1.appendSegment(int(seg))

    
    interest = Interest(name1)
    interest.setInterestLifetimeMilliseconds(3000)
    dump("Express name ", interest.toUri())
    face.expressInterest(interest, counter.onData, counter.onTimeout)
    
    """
    name2 = Name("/home/sensor/LED/T0829374723/turnOff")
    dump("Express name ", name2.toUri())
    face.expressInterest(name2, counter.onData, counter.onTimeout)
    """


    while counter._callbackCount < 1:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(2)

    face.shutdown()

main()
