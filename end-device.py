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
from pyndn.util import Blob


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Device(BaseNode):
    def __init__(self,configFileName,face):
        super(Device, self).__init__(configFileName=configFileName)
        
        #self.deviceSerial = self.getSerial()
        self._callbackCount = 0
	self._face = face

    def onData(self, interest, data):
        self._callbackCount += 1
	dump("Got data packet with name : ", data.getName().toUri())
        # Use join to convert each byte to chr.
        dump(data.getContent().toRawStr())

	#haven't checked symmetric key digest yet
	if (data.getName().toUri().startswith(self._bootstrapPrefix)):
	    self.onBootstrapData(interest, data) 

    def expressBootstrapInterest(self):
        symKey = "symmetricKeyForBootstrapping"
        
	#generate bootstrap name /home/controller/bootstrap/<device-parameters>
	bootstrapName = Name(device._bootstrapPrefix)

        deviceParameters = {}
        deviceParameters["category"] = "sensors"
        deviceParameters["id"] = "T123456789"
        bootstrapName.append(json.dumps(deviceParameters))

        bootstrapInterest = Interest(bootstrapName)

        bootstrapInterest.setInterestLifetimeMilliseconds(5000)

        bootstrapKeyLocator = KeyLocator()
        bootstrapKeyLocator.setType(KeyLocatorType.KEY_LOCATOR_DIGEST)
        bootstrapKeyLocator.setKeyData(symKey)
        bootstrapInterest.setKeyLocator(bootstrapKeyLocator)

	dump("Express interest :",bootstrapInterest.toUri())
        self._face.expressInterest(bootstrapInterest, self.onBootstrapData, self.onTimeout)
    
    def onBootstrapData(self, interest, data):
	dump("Data received.")
	content = json.loads(data.getContent().toRawStr(), encoding="latin-1")
	deviceNewIdentity = Name(content["deviceNewIdentity"])
	controllerIdentity = Name(content["controllerIdentity"])
	controllerPublicKeyInfo = content["controllerPublicKey"]

	#set new identity as default and generate default key-pair with KSK Certificate
	self._identityStorage.addIdentity(deviceNewIdentity)
	self._identityManager.setDefaultIdentity(deviceNewIdentity)
	try:
	    self._identityManager.getDefaultKeyNameForIdentity(deviceNewIdentity)
	except SecurityException:
	    #generate new key-pair and certificate for new identity
	    dump("Installed new identity as default\nGenerating new key-pair and self signed certificate...")
	    newKey = self._identityManager.generateRSAKeyPairAsDefault(Name(deviceNewIdentity), isKsk=True)
	    newCert = self._identityManager.selfSign(newKey)
	    self._identityManager.addCertificateAsIdentityDefault(newCert)
	
	#add controller's identity and public key
	keyType = controllerPublicKeyInfo["keyType"]
	keyName = Name(controllerPublicKeyInfo["keyName"])
	keyDer = Blob().fromRawStr(controllerPublicKeyInfo["publicKeyDer"])
	dump("KeyType: ",keyType)
	dump("keyName: ",keyName)
	dump("Controller public key der : ",keyDer)

	self._identityStorage.addIdentity(controllerIdentity)
	try:
	    self._identityStorage.addKey(keyName, keyType, keyDer)
	    dump("Controller's identity, key and certificate installled.")
	except SecurityException:
	    dump("Controller's identity, key, certificate already exists.")

	#express an certificate request interest
	defaultKeyName = self._identityManager.getDefaultKeyNameForIdentity(self._keyChain.getDefaultIdentity() )
	self.requestCertificate(defaultKeyName)


    def beforeLoopStart(self):
	pass	
	
    def onTimeout(self, interest):
        self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri())

    def requestCertificate(self, keyIdentity):
        """
        We compose a command interest with our public key info so the controller
        can sign us a certificate that can be used with other nodes in the network.
	Name format : /home/<device-category>/KEY/<device-id>/<key-id>/<publickey>/ID-CERT/<version-number>
	"""
	certificateRequestName = self._keyChain.getDefaultIdentity()
	deviceIdComponent = certificateRequestName.get(-1)
	keyIdComponent = keyIdentity.get(-1)

	certificateRequestName = certificateRequestName
	certificateRequestName.append("KEY")
	#certificateRequestName.append(deviceIdComponent)
	certificateRequestName.append(keyIdComponent)

	key = self._identityManager.getPublicKey(keyIdentity)
	keyInfo = {}
	keyInfo["keyType"] = key.getKeyType()
	keyInfo["keyDer"] = key.getKeyDer().toRawStr()

	certificateRequestName.append(json.dumps(keyInfo, encoding="latin-1"))

	certificateRequestName.append("ID-CERT")
	
	dump("Sending certificate request : ",certificateRequestName)

	self._face.expressInterest(Interest(certificateRequestName), self.onCertificateData, self.onTimeout)
	#TODO use symmetric key to sign
	
    def onCertificateData(self, interest, data):
	dump("OnCertificateData : ",data)
	

if __name__ == '__main__':
    face = Face("")

    device = Device("default.conf",face)
    
    device.expressBootstrapInterest()
    #device.requestCertificate(device._identityManager.getDefaultKeyNameForIdentity(device._keyChain.getDefaultIdentity() )) 

    while device._callbackCount < 1000:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

