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
import json
import Adafruit_DHT

class DHT22(Device):

    def __init__(self,configFileName=None):
        super(DHT22, self).__init__(configFileName)

        self._identity = "/home/sensor/DHT22/0"
        self._deviceProfile = DeviceProfile(category = "sensor", type_= "DHT22", serialNumber = "0")
        self.addCommands(['status'])
        self.sensor = 22
        self.pin = 18

    def status(self, interest, transport):
        h, t = Adafruit_DHT.read_retry(self.sensor, self.pin)
        h = round(h,2)
        t = round(t,2)
        result = {}
        result['temperature'] = str(t)
        result['humidity'] = str(h)

        data = Data(interest.getName())
        data.setContent(json.dumps(result))
        self.sendData(data, transport, sign=False)
        print ("status command. Sent data back.\n") 
    
    
  

if __name__ == "__main__":
    dht22 = DHT22()
    dht22.start()
