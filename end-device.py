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
import json
from pyndn import Name
from pyndn import Face
from pyndn import Interest
from pyndn import KeyLocator, KeyLocatorType
from base_node import BaseNode
from pyndn.security.security_exception import SecurityException


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Device(BaseNode):
    def __init__(self,configFileName):
        super(Device, self).__init__(configFileName=configFileName)
        
        #self.deviceSerial = self.getSerial()
        self._callbackCount = 0

    def onData(self, interest, data):
        self._callbackCount += 1
        dump("Got data packet with name", data.getName().toUri())
        # Use join to convert each byte to chr.
        dump(data.getContent().toRawStr())

    def beforeLoopStart(self):
	pass	
	
    def onTimeout(self, interest):
        self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri())

    def _sendCertificateRequest(self, keyIdentity):
        """
        We compose a command interest with our public key info so the controller
        can sign us a certificate that can be used with other nodes in the network.
        """

        #TODO: GENERATE A NEW PUBLIC/PRIVATE PAIR INSTEAD OF COPYING

if __name__ == '__main__':
    face = Face("")

    device = Device("default.conf")
    
    symKey = "symmetricKeyForBootStrapping"
    bootStrapName = Name("/home/controller/bootstrap")

    deviceParameters = {}
    deviceParameters["category"] = "sensors"
    deviceParameters["id"] = "T123456789"
    bootStrapName.append(json.dumps(deviceParameters))

    bootStrapInterest = Interest(bootStrapName)

    bootStrapInterest.setInterestLifetimeMilliseconds(5000)

    bootStrapKeyLocator = KeyLocator()
    bootStrapKeyLocator.setType(KeyLocatorType.KEY_LOCATOR_DIGEST)
    bootStrapKeyLocator.setKeyData(symKey)
    bootStrapInterest.setKeyLocator(bootStrapKeyLocator)

    dump("Express interest ",bootStrapInterest.toUri())
    face.expressInterest(bootStrapInterest, device.onData, device.onTimeout)
     

    while device._callbackCount < 100:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

