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
"""
This module uses access token method to sign, verfy, encrypt and decrypt data/interest. Besides, it generates and updates seed/command access token/access token. 

"""

class AccessControlManager(object):

    def __init__(self,  wireFormat=None):
        super(AccessControlManager, self).__init__()
	self.hmacHelper = HmacHelper("default", wireFormat)


    def signInterestWithAccessToken(self, interest, accessTokenName, accessToken):
	self.hmacHelper.setKey(accessToken)
        self.hmacHelper.signInterest(interest, accessTokenName)

    def verifyCommandInterestWithSeed(self, interest, seed):
	#TODO 
        command = interest.getName().get(4).getValue().toBytes()
	seedSequence = interest.getName().get(5).getValue().toBytes()
	commandSequence = interest.getName().get(6).getValue().toBytes()
        signature = self.hmacHelper.extractInterestSignature(interest)
	accessTokenName = signature.getKeyLocator().getKeyName()
        
	commandTokenName = interest.getName().getPrefix(5).append("token").append(commandSequence)
	print "command token name: ",commandTokenName.toUri()
	print "access token name: ",accessTokenName.toUri()

        commandToken = hmac.new(seed, commandTokenName.toUri(), sha256).digest()
	accessToken = hmac.new(commandToken, accessTokenName.toUri(), sha256).digest()
        
	self.hmacHelper.setKey(accessToken)
	return self.hmacHelper.verifyInterest(interest)

if __name__ == '__main__':
    a = AccessControlManager()
    seed = sha256("seed").digest()
    interest = Interest(Name("/home/sensor/LED/T12321/turnOn/1/2"))
    ctn = "/home/sensor/LED/T12321/turnOn/token/2"
    atn = ctn+"/user/Teng/07"
    print ctn
    print atn
    ct = hmac.new(seed,ctn,sha256).digest()
    at = hmac.new(ct,atn,sha256).digest()

    a.signInterestWithAccessToken(interest,atn,at)

    print a.verifyCommandInterestWithSeed(interest,seed)



