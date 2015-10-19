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
    def __init__(self,configFileName=None):
        super(Device, self).__init__(configFileName)
        
        #for test
        self._callbackCount = 0
        self._identity = "/home/default/default/000000000"
        self._deviceProfile = DeviceProfile(category = "default", type_="default", serialNumber = "000000000")
        self._bootstrapKey = HMACKey(0,0,"default","bootstrap")
        self._commands = []
        self._accessControlManager = AccessControlManager()
        self._configurationToken = HMACKey(0,0,"configurationToken","configurationToken")
        self._seed =  HMACKey(0,0,"default","seedName")

            self.name = Name("/UA-cs-718/device/light/1/service/status")
        self.seed = sha256("status").digest()
        self.accessTokenName = Name('/UA-cs-718/device/light/1/service/status/seed/0/device/switch/1/key/0').toUri()
        self.accessTokenKey = hmac.new(self.seed, self.accessTokenName, sha256).digest()
        self.accessToken = HMACKey(0,0,self.accessTokenKey,self.accessTokenName)

        self.start = 0
        self.end = 0
        self.s = 0
        self.a = AccessControlManager()

    def expressBootstrapInterest(self):
        
        #generate bootstrap name /home/controller/bootstrap/<device-parameters>
       
        interest = Interest(self.name)
        interest.setInterestLifetimeMilliseconds(3000)
        self.a.signInterestWithHMACKey(interest,self.accessToken)
        self.face.expressInterest(interest, self.onData, self.onTimeout)

        dump("Express bootstrap interest : ",interest.toUri())
        self.face.expressInterest(interest, self.onBootstrapData, self.onBootstrapTimeout)
        print "start:", time.time()
        self.start = time.time()
    
    def onBootstrapData(self, interest, data):
        self.end = time.time()
        print "end: ", time.time()
        self.s = self.start - self.end
        print "s: ",self.s
        self._callbackCount +=1 
        if self._callbackCount >= 100:
            exit(1)

        self.expressBootstrapInterest()
    
    def addCommands(self,commands):
        self._commands += commands

    def excuteCommand(self, command, interest, transport):
        getattr(self,command)(interest,transport)

    def beforeLoopStart(self):
        #self.face.registerPrefix('/home', self.onInterest, self.onRegisterFailed)
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
        
        self.expressBootstrapInterest()
        
    def onTimeout(self, interest):
        self._callbackCount += 1
        dump("Time out for interest", interest.getName().toUri())

    def onBootstrapTimeout(self, interest):
        self._callbackCount += 1
        self.expressBootstrapInterest()
        dump("Time out for bootstrap interest, send again", interest.getName().toUri())

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        """
        interestName = interest.getName()
        #dump("Received interest: ",interestName.toUri())
        try:
            command = interestName.get(5).toEscapedString()
            #dump("command: ",command)
        except:
            pass

        if ("profile" in interestName.toUri()):
            self.onProfileRequest(prefix, interest, transport, registeredPrefixId)

        elif (command in self._commands):
            self.excuteCommand(command, interest, transport)
        """
        
        self.excuteCommand('status', interest, transport)
            #if it is a command interest,verify it
            #dump("It is a command interest, verifying ... ")
            #if (self._accessControlManager.verifyCommandInterestWithSeed(interest,self._seed)):
            #    dump("Verified")
            #    self.excuteCommand(command, interest, transport)
            #else:
            #    dump("Not verified")
            #    self.excuteCommand(command, interest, transport)
    def onProfileRequest(self, prefix, interest, transport, registeredPrefixId):
        #TODO verification
        dump("Received profile request, verifying ...")
        if ( self._accessControlManager.verifyInterestWithHMACKey(interest, self._configurationToken) ):
            dump("Verified")
            interestName = interest.getName() 
       
            data = Data(interestName)
            content = {}
            content["deviceProfile"] = self._deviceProfile.__dict__

            content["commandList"] = self._commands 
            data.setContent(json.dumps(content, encoding="latin-1")) 

            self._accessControlManager.signDataWithHMACKey(data, self._configurationToken)
            self.sendData(data,transport,sign=False)
            dump("Send profile back : ", content)
        else:
            dump("Not verified")
        
        
    
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
   
    def onRegisterFailed(self, prefix):
        dump("Register failed for prefix", prefix.toUri())



if __name__ == '__main__':

    device = Device()
    device.start()
    
    






