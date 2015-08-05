
# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Weiwei Liu <summerwing10@gmail.com>
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

import os.path
from pyndn import Name
from device_storage import DeviceStorage
from device_profile import DeviceProfile
from hmac_key import HMACKey


class FillDatabaseForTest(object):
    def __init__(self, count = None):
        if count == None:
            self.count = 1
        else:
            self.count = count 
        if not "HOME" in os.environ:
            home = '.'
        else:
            home = os.environ["HOME"]

        dbDirectory = os.path.join(home, '.ndn')
        self.databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')

        if os.path.isfile(self.databaseFilePath):
            os.remove(self.databaseFilePath)

        self.storage = DeviceStorage()

    def fillDatabase(self):
        count = self.count
        prefixStrBase = 'home/sensor/LED/'
        serviceProfileNameBase = '/standard/sensor/simple-LED-control/v'
        commandNameBase = 'turn_on'
        commandNameBase2 = 'turn_off'
        for i in range(1, count+1):
             prefixStr = prefixStrBase + str(i)
             self.add_a_default_device(prefixStr)
             name = Name(prefixStr)
             deviceId = self.storage.getDeviceId(name)
             serviceProfileName = serviceProfileNameBase + str(i)
             self.storage.addServiceProfile(deviceId, serviceProfileName)

             commandName = commandNameBase + str(i)
             commandName2 = commandNameBase2 + str(i)
             commandToken = self.create_a_default_key(commandName)
             commandToken2 = self.create_a_default_key(commandName2)
             self.storage.addCommand(deviceId, commandName, commandToken)
             self.storage.addCommand(deviceId,commandName2,commandToken2)

    def add_a_default_device(self, prefixStr):
        name = Name(prefixStr)
        profile = DeviceProfile(prefix = name)
        seed = self.create_a_default_key('')
        configurationToken = self.create_a_default_key()
        self.storage.addDevice(profile, seed, configurationToken)

    def create_a_default_key(self, keyName = None):
        keyContent = 'this is key content'
        seed = HMACKey(0,0, keyContent, keyName)
        return seed

test = FillDatabaseForTest(8)
test.fillDatabase()
