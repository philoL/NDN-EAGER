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
from pyndn.key_locator import KeyLocator, KeyLocatorType

from pyndn.security import KeyChain
from base_node import BaseNode
from pyndn.security import SecurityException
from pyndn.util import Blob

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Controller(BaseNode):
    def __init__(self,configFileName):
        super(Controller, self).__init__(configFileName=configFileName)
        self._responseCount = 0
	self._symmetricKey = "symmetricKeyForBootstrapping"
	self._prefix = "/home/controller/id999"

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1

	interestName = interest.getName()

	#for bootstrap interest
	if(interestName.toUri().startswith(self._bootstrapPrefix) and interest.getKeyLocator().getKeyData().toRawStr() == self._symmetricKey):
  	    dump("Reveived bootstrap interest")
	    self.onBootstrapInterest(prefix, interest, transport, registeredPrefixId)   
        
    	elif ("KEY" in interestName.toUri() and "ID-CERT" in interestName.toUri()):
	    dump("Reveived certificate request interest")
	    self.onCertificateRequest(prefix, interest, transport, registeredPrefixId)

    def onBootstrapInterest(self, prefix, interest, transport, registeredPrefixId):
	
	interestName = interest.getName()
	deviceParameters = json.loads(interestName.get(3).getValue().toRawStr())
	deviceNewIdentity = Name("/home")
            
	#create new identity for device
        deviceNewIdentity.append(deviceParameters["category"])
        deviceNewIdentity.append(deviceParameters["id"])
	    
        #generate content
        content = {}
        content["deviceNewIdentity"] = deviceNewIdentity.toUri()
        content["controllerIdentity"] = self._prefix

        #get public key of controller
        pKeyName = self._identityManager.getDefaultKeyNameForIdentity(self._identityManager.getDefaultIdentity())
        pKey = self._identityManager.getPublicKey(pKeyName)

        pKeyInfo = content["controllerPublicKey"] = {}
        pKeyInfo["keyName"] = pKeyName.toUri()
        pKeyInfo["keyType"] = pKey.getKeyType()
        pKeyInfo["publicKeyDer"] = pKey.getKeyDer().toRawStr()
        dump("Sent content : ",content)
	      
	#TODO generate signature for data
	    
	#generate data package
	data = Data(interestName)
	data.setContent(json.dumps(content,encoding="latin-1"))
	#data.setSignature(signature)
        encodedData = data.wireEncode()
        transport.send(encodedData.toBuffer())


    def onCertificateRequest(self, prefix, interest, transport, registeredPrefixId):
	interestName = interest.getName()
	dump("interest name : ",interestName)
	
	keyName = interestName[:3]
	keyId = interestName.get(4)
	keyName.append(keyId)
	keyInfo = json.loads(interestName.get(5).getValue().toRawStr(),encoding="latin-1")
	keyType = keyInfo['keyType']
	keyDer = Blob().fromRawStr(keyInfo['keyDer'])

	dump("keyname: ",keyName)
	dump("keyType ",keyInfo['keyType'])
	dump("keyDer string",keyInfo['keyDer'])
	dump("keyDer",keyDer)

	#device and controller are on one mechine, so it needs to be done.
	self._identityManager.setDefaultIdentity(Name(self._prefix))
	try:
	    self._identityStorage.addKey(keyName, keyType, keyDer)
	except SecurityException:
	    dump("The public key for device already exists ")

	signedCertificate = self._identityManager._generateCertificateForKey(keyName)
	self._keyChain.sign(signedCertificate, self._identityManager.getDefaultCertificateName())
	self._identityManager.addCertificate(signedCertificate)
   	

	
	encodedData = signedCertificate.wireEncode()
        transport.send(encodedData.toBuffer())



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
	        self._identityManager.getDefaultKeyNameForIdentity(identityName)
	    except SecurityException:
	        newKey = self._identityManager.generateRSAKeyPairAsDefault(Name(self._prefix), isKsk=True)
	        newCert = self._identityManager.selfSign(newKey)
	        dump("generated new KSK certificate ", newCert)
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

    
    while controller._responseCount < 100:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

