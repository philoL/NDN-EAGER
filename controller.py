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


import time
import json
from pyndn import Name, Face, Interest, Data
from pyndn.key_locator import KeyLocator, KeyLocatorType
from hmac_helper import HmacHelper 

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
    def __init__(self,configFileName=None):
        super(Controller, self).__init__(configFileName=configFileName)
        self._responseCount = 0
        self._symmetricKey = "symmetricKeyForBootstrapping"
        self._prefix = "/home"
        self._identity = "/home/controller/id999"
        self._hmacHelper = HmacHelper(self._symmetricKey)


    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1
        interestName = interest.getName()
        dump("received interest : ",interestName.toUri())

        #for bootstrap interest
        #if(interestName.toUri().startswith(self._bootstrapPrefix) and interest.getKeyLocator().getKeyData().toRawStr() == self._symmetricKey):
        if ( interestName.toUri().startswith(self._bootstrapPrefix) ):
            dump("Received bootstrap interest")
	    self.onBootstrapInterest(prefix, interest, transport, registeredPrefixId)   
        
        elif ("KEY" in interestName.toUri() and "ID-CERT" in interestName.toUri()):
            dump("Reveived certificate request interest")
            self.onCertificateRequest(prefix, interest, transport, registeredPrefixId)



    def onBootstrapInterest(self, prefix, interest, transport, registeredPrefixId):
        if (self._hmacHelper.verifyInterest(interest)):
            self.log.info("Bootstrap interest verified")
            interestName = interest.getName()
            deviceParameters = json.loads(interestName.get(3).getValue().toRawStr())
            #TODO: register new DEVICE

    
            #create new identity for device
            deviceNewIdentity = Name("/home")
            deviceNewIdentity.append(deviceParameters["category"])
            deviceNewIdentity.append(deviceParameters["type"])
            deviceNewIdentity.append(deviceParameters["serialNumber"])
                
            #TODO seed encryption
            seed = "seed"
            seedSequence = 0
	    configurationTokenSequence = 0

            #generate content
            content = {}
            content["deviceNewIdentity"] = deviceNewIdentity.toUri()
            content["controllerIdentity"] = self._identity
            content["seed"] = seed
	    content["seedSequence"] = seedSequence
            content["configurationTokenSequence"] = configurationTokenSequence

            #get public key of controller
            pKeyName = self._identityManager.getDefaultKeyNameForIdentity(self._identityManager.getDefaultIdentity())
            pKey = self._identityManager.getPublicKey(pKeyName)

            pKeyInfo = content["controllerPublicKey"] = {}
            pKeyInfo["keyName"] = pKeyName.toUri()
            pKeyInfo["keyType"] = pKey.getKeyType()
            pKeyInfo["publicKeyDer"] = pKey.getKeyDer().toRawStr()
            dump("Sent content : ",content)
                  
                
            #generate data package
            data = Data(interestName)
            data.setContent(json.dumps(content,encoding="latin-1"))
	    self._hmacHelper.signData(data)
            self.sendData(data,transport,sign=False)
           
            #request for device profile
            self.expressProfileRequest(deviceNewIdentity)
        else: 
            self.log.info("Bootstrap interest not verified")


    def onCertificateRequest(self, prefix, interest, transport, registeredPrefixId):
        if (self._hmacHelper.verifyInterest(interest)):
            self.log.info("certificate request interest verified")
            interestName = interest.getName()
            dump("interest name : ",interestName)
            
            keyName = interestName[:3]
            keyId = interestName.get(4)
            keyName.append(keyId)
            keyInfo = json.loads(interestName.get(5).getValue().toRawStr(),encoding="latin-1")
            keyType = keyInfo['keyType']
            keyDer = Blob().fromRawStr(keyInfo['keyDer'])

            #dump("keyname: ",keyName)
            dump("keyType ",keyInfo['keyType'])
            dump("keyDer string",keyInfo['keyDer'])
            dump("keyDer",keyDer)

            #device and controller are on one mechine, so it needs to be done.
            self._identityManager.setDefaultIdentity(Name(self._identity))
            try:
                self._identityStorage.addKey(keyName, keyType, keyDer)
            except SecurityException:
                dump("The public key for device already exists ")

            signedCertificate = self._identityManager._generateCertificateForKey(keyName)
            self._keyChain.sign(signedCertificate, self._identityManager.getDefaultCertificateName())
            self._identityManager.addCertificate(signedCertificate)
            #self._hmacHelper.signData()

            #encodedData = signedCertificate.wireEncode()
            #transport.send(encodedData.toBuffer())
	    self.sendData(signedCertificate,transport,sign=False)

	    self.log.info("Certificate sent back : {}".format(signedCertificate.__str__))
	    print(signedCertificate)
        else:
            self.log.info("certificate request interest not verified")
        
    def expressProfileRequest(self,deviceName):
       #TODO add nonce component afterwards
        profileRequest = Interest(deviceName.append("profile"))
        profileRequest.setInterestLifetimeMilliseconds(3000)
        dump("Request device Profile: ", profileRequest.toUri())
        
        self.face.expressInterest(profileRequest, self.onProfile, self.onProfileRequestTimeout)
    
    def onProfile(self, interest, data):
        dump("Profile received")
        #TODO verify data using configuration key
        deviceProfile = json.loads(data.getContent().toRawStr(), encoding="latin-1")
        dump(deviceProfile) 

    def onTimeout(self, interest):
        dump("Time out for interest", interest.getName().toUri()) 

    def onProfileRequestTimeout(self, interest):
        dump("Time out for device profile request, send again")        
        self.face.expressInterest(interest, self.onProfile, self.onProfileRequestTimeout)

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

    def beforeLoopStart(self):
        identityName = Name(self._identity)
        
        defaultIdentityExists = True
        try:
            defaultIdentityName = self._identityManager.getDefaultIdentity()
        except:
            defaultIdentityExists = False

        if not defaultIdentityExists or self._identityManager.getDefaultIdentity() != identityName:
            #make one
            dump("Create identity and certificate for identity name: ",identityName)
            self._keyChain.createIdentityAndCertificate(identityName)
       	    self._identityManager.setDefaultIdentity(identityName)

	self.face.setCommandSigningInfo(self._keyChain, self._keyChain.getDefaultCertificateName())
        self.face.registerPrefix(self._prefix, self.onInterest, self.onRegisterFailed)
        
        


if __name__ == '__main__':

    controller = Controller("default.conf")
    controller.start()
    #controller.beforeLoopStart()
    

    #face = Face()
    #controller.setFace(face)

    #face.setCommandSigningInfo(controller._keyChain, controller.getDefaultCertificateName())
    #face.registerPrefix(controller._prefix, controller.onInterest, controller.onRegisterFailed)
    #dump("Register prefix : ",controller._prefix)
    #while True:
    #    face.processEvents()
#	time.sleep(0.05)

 #   face.shutdown()




    


