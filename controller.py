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
from hmac_key import HMACKey
import hmac 
from hashlib import sha256
from device_profile import  DeviceProfile

from pyndn.security import KeyChain
from base_node import BaseNode
from pyndn.security import SecurityException
from pyndn.util import Blob
from device_user_access_manager import DeviceUserAccessManager
from access_control_manager import AccessControlManager


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class Controller(BaseNode):
    def __init__(self,configFileName=None):
        super(Controller, self).__init__(configFileName=configFileName)
        self._responseCount = 0

        self._bootstrapKey = HMACKey(0,0,"default","bootstrap")
        self._prefix = "/home"
        self._identity = "/home/controller/id999"

        self._accessControlManager = AccessControlManager()
        self._deviceUserAccessManager = DeviceUserAccessManager()
        self._deviceDict = {}

        #device dict (deviceProfile, seed, configurationToken, commandList, serviceProfileList)
        self._newDevice = {}
        self._newDevice['deviceProfile'] = None
        self._newDevice['seed'] = None
        self._newDevice['configurationToken'] = None
        self._newDevice['commandList'] = []

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1
        interestName = interest.getName()
        dump("Received interest : ",interestName.toUri())

        #for bootstrap interest
        if ( "bootstrap" in interestName.toUri()):
            dump("It is a bootstrap interest")
            self.onBootstrapInterest(prefix, interest, transport, registeredPrefixId)   
        
        elif ("KEY" in interestName.toUri() and "ID-CERT" in interestName.toUri()):
            dump("It is a certificate request interest")
            self.onCertificateRequest(prefix, interest, transport, registeredPrefixId)
        elif ("login" in interestName.toUri()):
            dump("It is a login interest")
            self.onLoginInterest(prefix, interest, transport, registeredPrefixId)

    def onLoginInterest(self, prefix, interest, transport, registeredPrfixId):
     
        interestName = interest.getName()
        username = interestName.get(3).getValue().toRawStr()
        content = ""
        if username != "guest":
            prefix = Name("/home/user/"+username)
            hash_ = self._deviceUserAccessManager.getUserHash(prefix)
            userHMACKey = HMACKey("0","0",hash_,"userHMACKey")

            if ( self._accessControlManager.verifyInterestWithHMACKey(interest, userHMACKey) ):
                content = "success"
            else:
                content = "invalide username or password"
            
            data = Data(interestName)
            data.setContent(content)
            dump(content)
            self._accessControlManager.signDataWithHMACKey(data,userHMACKey)
            self.sendData(data,transport,sign=False)

        else:
            #TODO guest mode
            pass
    
   
    def onBootstrapInterest(self, prefix, interest, transport, registeredPrefixId):
        
        if ( self._accessControlManager.verifyInterestWithHMACKey(interest, self._bootstrapKey) ):
            dump("Verified")
            interestName = interest.getName()
            deviceParameters = json.loads(interestName.get(3).getValue().toRawStr())

            #create new identity for device
            deviceNewIdentity = Name("home")
            deviceNewIdentity.append(deviceParameters["category"])
            deviceNewIdentity.append(deviceParameters["type"])
            deviceNewIdentity.append(deviceParameters["serialNumber"])

            seedSequence = 0
            configurationTokenSequence = 0
            seed = HMACKey(0,0,"seed","seedName")

            if (deviceNewIdentity.toUri() in self._deviceDict.keys()):
                dump("The device is already registered. No need to add again.")
            else:
                dump("Adding the new device...")
                self._newDevice["seed"] = seed

                #generate configuration token
                configurationTokenName = self._identity+"/"+str(configurationTokenSequence)
                configurationTokenKey = hmac.new(seed.getKey(), configurationTokenName, sha256).digest()
                configurationToken = HMACKey(configurationTokenSequence,0,configurationTokenKey,configurationTokenName)

                self._newDevice["configurationToken"] = configurationToken

            #generate content
            #TODO seed encryption

            content = {}
            content["deviceNewIdentity"] = deviceNewIdentity.toUri()
            content["controllerIdentity"] = self._identity
            content["seed"] = seed.getKey()
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
            self._accessControlManager.signDataWithHMACKey(data,self._bootstrapKey)
            self.sendData(data,transport,sign=False)
           
            #request for device profile
            self.expressProfileRequest(deviceNewIdentity)
        else: 
            self.log.info("Bootstrap interest not verified")


    def onCertificateRequest(self, prefix, interest, transport, registeredPrefixId):
        if (self._hmacHelper.verifyInterest(interest)):
            dump("certificate request interest verified")
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

            self.sendData(signedCertificate,transport,sign=False)

            dump("Certificate sent back : {}".format(signedCertificate.__str__))
	    print(signedCertificate)
        else:
            self.log.info("certificate request interest not verified")
        
    def expressProfileRequest(self,deviceName):
        
        profileRequest = Interest(deviceName.append("profile"))
        profileRequest.setInterestLifetimeMilliseconds(3000)
        dump("Request device Profile: ", profileRequest.toUri())

        #sign profile request with configuration token
        self._accessControlManager.signInterestWithHMACKey(profileRequest,self._newDevice['configurationToken'])
        
        self.face.expressInterest(profileRequest, self.onProfile, self.onProfileRequestTimeout)
    
    def onProfile(self, interest, data):
        dump("Profile received, verifying ...")
        if ( self._accessControlManager.verifyInterestWithHMACKey(interest, self._newDevice['configurationToken']) ):
            dump("Verified.")
              
            #load content
            content = json.loads(data.getContent().toRawStr(), encoding="latin-1")

            #load deviceProfile " 'prefix', 'location', 'manufacturer', 'category', 'type', 'model', 'serialNumber', 'serviceProfileList'"
            deviceProfileDict = content['deviceProfile']
            prefix = deviceProfileDict['_prefix']
            location = deviceProfileDict['_location']
            manufacturer = deviceProfileDict['_manufacturer']
            category = deviceProfileDict['_category']
            _type = deviceProfileDict['_type']
            model = deviceProfileDict['_model']
            serialNumber = deviceProfileDict['_serialNumber']
            serviceProfileList = deviceProfileDict['_serviceProfileList'] 

            self._newDevice['deviceProfile'] = DeviceProfile(prefix, location, manufacturer,
                category, _type, model, serialNumber, serviceProfileList)

            dump("device profile ",self._newDevice['deviceProfile'])

            #load command list
            self._newDevice['commandList'] = content['commandList']
            dump("commandList ",self._newDevice['commandList'])

            #add newDevice into self._deviceDict 
            self._deviceDict[prefix] = self._newDevice

            #add device to DB
            

            try:
                self._deviceUserAccessManager.createDevice(self._newDevice['deviceProfile'], self._newDevice['seed'],
                        self._newDevice['configurationToken'], self._newDevice['commandList'])
                dump("Creating a new device into DB")
            except RuntimeError:
                dump("Ooops... The device is already in DB. There is no need to add one more")  

            
        else:
            dump("Not verified.") 


    def onTimeout(self, interest):
        dump("Time out for interest", interest.getName().toUri()) 

    def onProfileRequestTimeout(self, interest):
        dump("Time out for device profile request, send again")        
        interestName = interest.getName().getPrefix(-2)
        profileRequest = Interest(interestName)
        profileRequest.setInterestLifetimeMilliseconds(3000)
       
        self._accessControlManager.signInterestWithHMACKey(profileRequest,self._newDevice['configurationToken'])
        self.face.expressInterest(profileRequest, self.onProfile, self.onProfileRequestTimeout)

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





    


