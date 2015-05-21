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
from pyndn import Data
from pyndn import Face
from pyndn.security import KeyChain
from base_node import BaseNode


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Controller(BaseNode):
    def __init__(self,configFileName):
        super(Controller, self).__init__(configFileName=configFileName)
        self._responseCount = 0
	self._symmetricKey = "symmetricKeyForBootStrapping"
	self._prefix = "/home/controller"
	self._bootStrapPrefix = "/home/controller/bootstrap"

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1
	
	interestName = interest.getName()
        dump("Received interest ", interestName.toUri())

	if(interestName.toUri().startswith(self._bootStrapPrefix) and interest.getKeyLocator().getKeyData().toRawStr() == self._symmetricKey):
  	    
	    deviceParameters = json.loads(interestName.get(3).getValue().toRawStr())
	    deviceNewIdentity = Name("/home")
            
	    #create new identity for device
	    deviceNewIdentity.append(deviceParameters["category"])
	    deviceNewIdentity.append(deviceParameters["id"])
	    dump("New identity for device: ",deviceNewIdentity)
	    
	    #create key-pair and certificate for new identity
	    self.

	    data = Data(interestName)
	    content = {}
	    content["deviceNewIdentity"] = deviceNewIdentity.toUri()
	    content[]
	    content["controllerPublicKey"] = 

	
		#dump("Send data : ",content)
		#data = Data(interest.getName())
        	#data.setContent(content)
        	#self._keyChain.sign(data, self._certificateName)
        	#encodedData = data.wireEncode()
        #dump("Sent content", content)
        #transport.send(encodedData.toBuffer())

    
    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

    def beforeLoopStart(self):
	identityName = Name(self._prefix)
	
	defaultIdentityExists = True
	try:
	    defaultIdentityName = self._identityManager.getDefaultIdentity()
	except:
	    defaultIdentityExists = False
	    

	#dump(self._identityManager.getDefaultKeyNameForIdentity(self._prefix))
	if not defaultIdentityExists or self._identityManager.getDefaultIdentity() != identityName:
	    #make one
	    dump("Set default identity: ",identityName)
	    #self._identityManager.createIdentityAndCertificate(identityName)
	    self._identityStorage.addIdentity(identityName)
	    self._identityManager.setDefaultIdentity(identityName)

	    try:
	        getDefaultKeyNameForIdentity(identityName)
	    except:
	        newKey = self._identityManager.generateRSAKeyPairAsDefault(Name(self._prefix), isKsk=True)
	        newCert = self._identityManager.selfSign(newKey)
	        dump("new certificate", newCert)
	        self._identityManager.addCertificateAsIdentityDefault(newCert)


if __name__ == '__main__':

    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Use the system default key chain and certificate name to sign commands.
    
    controller = Controller("default.conf")
    controller.beforeLoopStart()
    
    face.setCommandSigningInfo(controller.getKeyChain(), controller._keyChain.getDefaultCertificateName())

    # Also use the default certificate name to sign data packets.

    prefix = Name("/home/")
    dump("Register prefix", prefix)

    face.registerPrefix(prefix, controller.onInterest, controller.onRegisterFailed)

    identityName = controller._identityManager.getDefaultIdentity()
    keyName = controller._identityManager.getDefaultKeyNameForIdentity(identityName)
	
    key = controller._identityManager.getPublicKey(keyName)
    #dump("key : ",key.getKeyDer().toHex())
    
    while controller._responseCount < 100:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

