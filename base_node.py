
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Adeola Bannis <thecodemaiden@gmail.com>
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
import logging
import time
import sys
import random

from pyndn import Name, Face, Interest, Data, ThreadsafeFace
from pyndn.security.policy import ConfigPolicyManager
from pyndn.security import KeyChain
from pyndn.security.identity import IdentityManager, BasicIdentityStorage
from pyndn.security.security_exception import SecurityException
    

from collections import namedtuple

try:
    import asyncio
except ImportError:
    import trollius as asyncio

#Command = namedtuple('Command', ['suffix', 'function', 'keywords', 'isSigned'])

class BaseNode(object):
    """
    This class contains methods/attributes common to both end device and controller.
    
    """
    def __init__(self,configFileName):
        """
        Initialize the network and security classes for the node
        """
        super(BaseNode, self).__init__()

	
        self._identityStorage = BasicIdentityStorage()
        self._identityManager = IdentityManager(self._identityStorage)
        self._policyManager = ConfigPolicyManager(configFileName)

        # hopefully there is some private/public key pair available
        self._keyChain = KeyChain(self._identityManager,self._policyManager)

        self._registrationFailures = 0
        self._prepareLogging()

        self._setupComplete = False
        self._instanceSerial = None

        # waiting devices register this prefix and respond to discovery
        # or configuration interest
        self._bootstrapPrefix = '/home/controller/bootstrap'

    def getSerial(self):
        """
         Since you may wish to run two nodes on a Raspberry Pi, each
         node will generate a unique serial number each time it starts up.
        """
        if self._instanceSerial is None:
            prefixLen = 4
            prefix = ''
            for i in range(prefixLen):
                prefix += (chr(random.randint(0,0xff)))
        
            self._instanceSerial = prefix.encode('hex')
        return self._instanceSerial

##
# Logging
##
    def _prepareLogging(self):
        self.log = logging.getLogger(str(self.__class__))
        self.log.setLevel(logging.DEBUG)
        logFormat = "%(asctime)-15s %(name)-20s %(funcName)-2s (%(levelname)-2s):\t%(message)s"
        self._console = logging.StreamHandler()
        self._console.setFormatter(logging.Formatter(logFormat))
        self._console.setLevel(logging.INFO)
        # without this, a lot of ThreadsafeFace errors get swallowed up
        logging.getLogger("trollius").addHandler(self._console)
        self.log.addHandler(self._console)

    def setLogLevel(self, level):
        """
        Set the log level that will be output to standard error
        :param level: A log level constant defined in the logging module (e.g. logging.INFO) 
        """
        self._console.setLevel(level)

    def getLogger(self):
        """
        :return: The logger associated with this node
        :rtype: logging.Logger
        """
        return self.log

###
# Startup and shutdown
###
    def beforeLoopStart(self):
        """
        Called before the event loop starts.
        """
        pass
    
    def getKeyChain(self):
        return self._keyChain

    def getDefaultIdentity(self):
        try:
            defaultIdentity = self._identityManager.getDefaultIdentity()
        except SecurityException:
            defaultIdentity = ""

        return defaultIdentity


    def getDefaultCertificateName(self):
        #exception - no certficate, return ''

        try:
            certName = self._identityStorage.getDefaultCertificateNameForIdentity( 
            self._identityManager.getDefaultIdentity())
        except SecurityException:
            certName = ""

        return certName

    def start(self):
        """
        Begins the event loop. After this, the node's Face is set up and it can
        send/receive interests+data
        """
        self.log.info("Starting up")
        self.loop = asyncio.get_event_loop()
        self.face = ThreadsafeFace(self.loop, '')
       
        self._keyChain.setFace(self.face)

        self._isStopped = False
        self.face.stopWhen(lambda:self._isStopped)
        
        self.beforeLoopStart()

        self.face.setCommandSigningInfo(self._keyChain, self.getDefaultCertificateName())

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log.exception(e, exc_info=True)
        finally:
            self._isStopped = True

    def stop(self):
        """
        Stops the node, taking it off the network
        """
        self.log.info("Shutting down")
        self._isStopped = True 
        
###
# Data handling
###
    def signData(self, data):
        """
        Sign the data with our network certificate
        :param pyndn.Data data: The data to sign
        """
        self._keyChain.sign(data, self.getDefaultCertificateName())

    def sendData(self, data, transport, sign=True):
        """
        Reply to an interest with a data packet, optionally signing it.
        :param pyndn.Data data: The response data packet
        :param pyndn.Transport transport: The transport to send the data through. This is 
            obtained from an incoming interest handler
        :param boolean sign: (optional, default=True) Whether the response must be signed. 
        """
        if sign:
            self.signData(data)
        transport.send(data.wireEncode().buf())

###
# 
# 
##
    def onRegisterFailed(self, prefix):
        """
        Called when the node cannot register its name with the forwarder
        :param pyndn.Name prefix: The network name that failed registration
        """
        if self._registrationFailures < 5:
            self._registrationFailures += 1
            self.log.warn("Could not register {}, retry: {}/{}".format(prefix.toUri(), self._registrationFailures, 5)) 
            self.face.registerPrefix(self.prefix, self._onCommandReceived, self.onRegisterFailed)
        else:
            self.log.critical("Could not register device prefix, ABORTING")
            self._isStopped = True

    def verificationFailed(self, dataOrInterest):
        """
        Called when verification of a data packet or command interest fails.
        :param pyndn.Data or pyndn.Interest: The packet that could not be verified
        """
        self.log.info("Received invalid" + dataOrInterest.getName().toUri())

    @staticmethod
    def getDeviceSerial():
        """
        Find and return the serial number of the Raspberry Pi. Provided in case
        you wish to distinguish data from nodes with the same name by serial.
        :return: The serial number extracted from device information in /proc/cpuinfo
        :rtype: str
        """
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[1].strip()


