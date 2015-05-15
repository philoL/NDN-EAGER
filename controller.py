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

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1
	
	interestName = interest.getName()
        dump("Received interest ", interestName)
        
	componentsString = []
	for eachComponent in interestName._components:
	    componentsString.append(eachComponent.toEscapedString())
	if (len(componentsString) >= 6 and componentsString[0] == "home" and componentsString[1] == "controller" and componentsString[2] == "bootstrap"):
	        
	    newDeviceCategory = componentsString[3];
	    newDeviceId = componentsString[4];
	    signature = componentsString[5];
	
	    if (signature == self._symmetricKey):
	        #newDeviceIdentityName = Name("/home"+newDeviceCategory+newDeviceId)
		content = "/home/"+newDeviceCategory+"/"+newDeviceId+"/"
		#content = content + "/"
		identityName = self._identityManager.getDefaultIdentity()
		keyName = self._identityManager.getDefaultKeyNameForIdentity(identityName)
		key = self._identityManager.getPublicKey(keyName)
		content = content+key.getKeyDer().toHex()
		
		dump("Send data : ",content)
		data = Data(interest.getName())
        	data.setContent(content)
        	#self._keyChain.sign(data, self._certificateName)
        	encodedData = data.wireEncode()

        #dump("Sent content", content)
        transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

    def beforeLoopStart(self):
	identityName = Name(self._prefix)
	dump(identityName)
	defaultIdentityExist = True
	try:
	    defaultIdentityName = self._identityManager.getDefaultIdentity()
	    dump(self._identityManager.getDefaultIdentity())
	    dump(self._identityManager.getDefaultKeyNameForIdentity(defaultIdentityName))
	except:
	    defaultIdentityExist = False
	    

	#dump(self._identityManager.getDefaultKeyNameForIdentity(self._prefix))
	if not defaultIdentityExist or self._identityManager.getDefaultIdentity() != identityName:
	    #make one
	    self._identityManager.setDefaultIdentity(identityName)
	    self.log.warn("Generating controller key pair(this would take a while)......")
	    newKey = self._identityManager.generateRSAKeyPairAsDefault(Name(self._prefix), isKsk=True)
	    newCert = self._identityManager.selfSign(newKey)
	    self._identityManager.addCertificateAsDefault(newCert)


if __name__ == '__main__':

    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Use the system default key chain and certificate name to sign commands.
    
    controller = Controller("default.conf")
    controller.beforeLoopStart()
    
    face.setCommandSigningInfo(controller.getKeyChain(), controller.getDefaultCertificateName())

    # Also use the default certificate name to sign data packets.

    prefix = Name("/home/")
    dump("Register prefix", prefix)

    face.registerPrefix(prefix, controller.onInterest, controller.onRegisterFailed)

    identityName = controller._identityManager.getDefaultIdentity()
    keyName = controller._identityManager.getDefaultKeyNameForIdentity(identityName)
	
    key = controller._identityManager.getPublicKey(keyName)
    dump("key : ",key.getKeyDer().toHex())
    
    while controller._responseCount < 100:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

