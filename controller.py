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
    def __init__(self):
        super(Controller, self).__init__()
        self._responseCount = 0

    def onInterest(self, prefix, interest, transport, registeredPrefixId):
        self._responseCount += 1

        dump("interest ", interest.getName())
        dump("Uri ", interest.getName().toUri())
        # Make and sign a Data packet.
        #data = Data(interest.getName())
        content = "Echo " + interest.getName().toUri()
        #data.setContent(content)
        #self._keyChain.sign(data, self._certificateName)
        #encodedData = data.wireEncode()

        #dump("Sent content", content)
        #transport.send(encodedData.toBuffer())

    def onRegisterFailed(self, prefix):
        self._responseCount += 1
        dump("Register failed for prefix", prefix.toUri())

if __name__ == '__main__':

    # The default Face will connect using a Unix socket, or to "localhost".
    face = Face()

    # Use the system default key chain and certificate name to sign commands.
    
    controller = Controller()
    face.setCommandSigningInfo(controller.getKeyChain(), controller.getDefaultCertificateName())

    # Also use the default certificate name to sign data packets.

    prefix = Name("/home/")
    dump("Register prefix", prefix.toUri())
    face.registerPrefix(prefix, controller.onInterest, controller.onRegisterFailed)

    while controller._responseCount < 100:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(0.01)

    face.shutdown()

