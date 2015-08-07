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
This module gives an example of LED instance
"""

from device import Device
from device_profile import DeviceProfile
import RPi.GPIO as GPIO
from pyndn import Data

class LED(Device):

    def __init__(self,configFileName=None):
        super(LED, self).__init__(configFileName)
        
	self._deviceProfile = DeviceProfile(category = "sensors", type_= "LED", serialNumber = "T0829374723")
        self.addCommands(['turnOn','turnOff','readStatus'])

    def turnOn(self, interest, transport):
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
        GPIO.setup(17,GPIO.OUT)        	    
        GPIO.setup(16,GPIO.OUT) 
        GPIO.setup(21,GPIO.OUT)
        print("Command turnOn is excuted, the light is on.")

        GPIO.output(17,GPIO.HIGH)
        GPIO.output(16,GPIO.HIGH)
        GPIO.output(21,GPIO.HIGH)

        
        data = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
  
    def turnOff(self, interest, transport):
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
        GPIO.setup(17,GPIO.OUT)        	    
        GPIO.setup(16,GPIO.OUT) 
        GPIO.setup(21,GPIO.OUT)
        print("Command turnOff is excuted, the light is off.")

        GPIO.output(17,GPIO.LOW)
        GPIO.output(16,GPIO.LOW)
        GPIO.output(21,GPIO.LOW)

        data = Data(interest.getName())
        data.setContent("success")
        self.sendData(data, transport, sign=False)
        print("msg success sent back")
  

if __name__ == "__main__":
    led = LED()
    led.start()
