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
from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn import KeyLocator, KeyLocatorType
from base_node import BaseNode
from hmac_helper import HmacHelper 
from pyndn.security.security_exception import SecurityException
from pyndn.util import Blob
try:
    import asyncio
except ImportError:
    import trollius as asyncio

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Device(BaseNode):
    def __init__(self,configFileName):
        super(Device, self).__init__(configFileName=configFileName)
        
        self._deviceSerial = self.getSerial()
        self._callbackCount = 0
        self._symKey = "symmetricKeyForBootstrapping"
        self._category = "sensors"
        self._id = "T9273659"
        self._hmacHelper = HmacHelper(self._symKey)


    def expressBootstrapInterest(self):
        
        #generate bootstrap name /home/controller/bootstrap/<device-parameters>
        bootstrapName = Name(self._bootstrapPrefix)

        deviceParameters = {}
        deviceParameters["category"] = self._category
        deviceParameters["id"] = self._id
        bootstrapName.append(json.dumps(deviceParameters))

        bootstrapInterest = Interest(bootstrapName)
        bootstrapInterest.setInterestLifetimeMilliseconds(5000)
        #bootstrapKeyLocator = KeyLocator()
        #bootstrapKeyLocator.setType(KeyLocatorType.KEY_LOCATOR_DIGEST)
        #bootstrapKeyLocator.setKeyData(self._symKey)
        #bootstrapInterest.setKeyLocator(bootstrapKeyLocator)
        self._hmacHelper.signInterest(bootstrapInterest)

        dump("Express bootstrap interest : ",bootstrapInterest.toUri())
        self.face.expressInterest(bootstrapInterest, self.onBootstrapData, self.onTimeout)
    def onInterest():
        pass
    def onRegisterFailed():
	pass
    
    def onBootstrapData(self, interest, data):
        dump("Bootstrap data received.")

        if (self._hmacHelper.verifyData(data)):
            self.log.info("Bootstrap data is verified")
            content = json.loads(data.getContent().toRawStr(), encoding="latin-1")
            deviceNewIdentity = Name(content["deviceNewIdentity"])
            controllerIdentity = Name(content["controllerIdentity"])
            controllerPublicKeyInfo = content["controllerPublicKey"]

            self.face.registerPrefix(content["deviceNewIdentity"],self.onInterest,self.onRegisterFailed)
            #set new identity as default and generate default key-pair with KSK Certificate
            self._identityStorage.addIdentity(deviceNewIdentity)
            self._identityManager.setDefaultIdentity(deviceNewIdentity)
            try:
                self._identityManager.getDefaultKeyNameForIdentity(deviceNewIdentity)
            except SecurityException:
                #generate new key-pair and certificate for new identity
                dump("Install new identity as default\nGenerate new key-pair and self signed certificate")
                newKey = self._identityManager.generateRSAKeyPairAsDefault(Name(deviceNewIdentity), isKsk=True)
                newCert = self._identityManager.selfSign(newKey)
                self._identityManager.addCertificateAsIdentityDefault(newCert)
            
            #add controller's identity and public key
            keyType = controllerPublicKeyInfo["keyType"]
            keyName = Name(controllerPublicKeyInfo["keyName"])
            keyDer = Blob().fromRawStr(controllerPublicKeyInfo["publicKeyDer"])
            dump("Controller's KeyType: ",keyType)
            dump("Controller's keyName: ",keyName)
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
        else:
            self.log.info("Bootstrap data is not verified")
        
        


    def beforeLoopStart(self):
        self.face.registerPrefix('/home', self.onInterest, self.onRegisterFailed)
        self.expressBootstrapInterest()
        
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

        certificateRequest = Interest(certificateRequestName)
        certificateRequest.setInterestLifetimeMilliseconds(5000)
        self._hmacHelper.signInterest(certificateRequest)
        
        dump("Sending certificate request : ",certificateRequestName)

        self.face.expressInterest(certificateRequest, self.onCertificateData, self.onTimeout)
        #TODO use symmetric key to sign
        
    def onCertificateData(self, interest, data):
        dump("OnCertificateData : ",data)
        

if __name__ == '__main__':

    device = Device("tmp.conf")
    device.start()
    
    

