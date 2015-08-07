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
from hmac_helper import HmacHelper 
from pyndn.encoding import WireFormat
from pyndn.util import Blob
from pyndn import Data, KeyLocatorType,Interest,Name
from hashlib import sha256
import hmac
from hmac_key import HMACKey
"""
This module uses access token method to sign, verfy, encrypt and decrypt data/interest. Besides, it generates and updates seed/command access token/access token. 

"""
def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class AccessControlManager(object):

    def __init__(self,  wireFormat=None):
        super(AccessControlManager, self).__init__()
        self.hmacHelper = HmacHelper("default", wireFormat)


    def signInterestWithHMACKey(self, interest, hmacKey):
        self.hmacHelper.setKey(hmacKey.getKey())
        self.hmacHelper.signInterest(interest, hmacKey.getName())


    def verifyInterestWithHMACKey(self, interest, hmacKey):
        self.hmacHelper.setKey(hmacKey.getKey())
        return self.hmacHelper.verifyInterest(interest)

    def signDataWithHMACKey(self, data, hmacKey):
    	self.hmacHelper.setKey(hmacKey.getKey())
        self.hmacHelper.signData(data,hmacKey.getName())

    def verifyDataWithHMACKey(self, data, hmacKey):
        self.hmacHelper.setKey(hmacKey.getKey())
        return self.hmacHelper.verifyData(data)

    def verifyCommandInterestWithSeed(self, interest, seed):
        """
        seed is a HMACKey.
        """
        try:
        #try to fetch command, seedSequence and commandSequence
	    	command = interest.getName().get(4).getValue().toBytes()
	    	seedSequence = interest.getName().get(5).getValue().toBytes()
	    	commandSequence = interest.getName().get(6).getValue().toBytes()
	    	signature = self.hmacHelper.extractInterestSignature(interest)
	    	accessTokenName = signature.getKeyLocator().getKeyName()
        except Exception:
            return False


        commandTokenName = interest.getName().getPrefix(5).append("token").append(commandSequence)
        commandToken = hmac.new(seed.getKey(), commandTokenName.toUri(), sha256).digest()
        accessToken = hmac.new(commandToken, accessTokenName.toUri(), sha256).digest()

        
        #dump("seed.getKey() :",seed.getKey())
        #dump("commandTokenName :",commandTokenName)
        #dump("commandTokenKey :",commandToken)
        #dump("accessTokenName :",accessTokenName)
        #dump("accessTokenKey :",accessToken)

        self.hmacHelper.setKey(accessToken)

        return self.hmacHelper.verifyInterest(interest)




