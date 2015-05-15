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
from pyndn import Face
from base_node import BaseNode
import CertificateRequestMessage

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
        makeKey = False
        try:
            defaultKey = self._identityStorage.getDefaultKeyNameForIdentity(keyIdentity)
            newKeyName = defaultKey
        except SecurityException:
            defaultIdentity = self._keyChain.getDefaultIdentity()
            defaultKey = self._identityStorage.getDefaultKeyNameForIdentity(defaultIdentity)
            newKeyName = self._identityStorage.getNewKeyName(keyIdentity, True)
            makeKey = True
             
        self.log.debug("Found key: " + defaultKey.toUri()+ " renaming as: " + newKeyName.toUri())

        keyType = self._identityStorage.getKeyType(defaultKey)
        keyDer = self._identityStorage.getKey(defaultKey)

        if makeKey:
            try:
                privateDer = self._identityManager.getPrivateKey(defaultKey)
            except SecurityException:
                # XXX: is recovery impossible?
                pass
            else:
                try:
                    self._identityStorage.addKey(newKeyName, keyType, keyDer)
                    self._identityManager.addPrivateKey(newKeyName, privateDer)
                except SecurityException:
                    # TODO: key shouldn't exist...
                    pass

        message = CertificateRequestMessage()
        message.command.keyType = keyType
        message.command.keyBits = keyDer.toRawStr()

        for component in range(newKeyName.size()):
            message.command.keyName.components.append(newKeyName.get(component).toEscapedString())

        paramComponent = ProtobufTlv.encode(message)

        interestName = Name(self._policyManager.getTrustRootIdentity()).append("certificateRequest").append(paramComponent)
        interest = Interest(interestName)
        interest.setInterestLifetimeMilliseconds(10000) # takes a tick to verify and sign
        self._hmacHandler.signInterest(interest, keyName=self.prefix)

        self.log.info("Sending certificate request to controller")
        self.log.debug("Certificate request: "+interest.getName().toUri())
        self.face.expressInterest(interest, self._onCertificateReceived, self._onCertificateTimeout)

if __name__ == '__main__':
    face = Face("")

    device = Device("default.conf")
    
    symKey = "symmetricKeyForBootStrapping"
    bootStrapName = Name("/home/controller/bootstrap/light/id1/"+symKey)
    dump("Express name ",bootStrapName.toUri())
    
    face.expressInterest(bootStrapName, device.onData, device.onTimeout)


    while device._callbackCount < 10:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

