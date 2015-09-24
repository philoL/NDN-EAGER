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

import unittest as ut
import os.path
from pyndn import Name
from device_user_access_manager import DeviceUserAccessManager
from device_profile import DeviceProfile
from hmac_key import HMACKey

class TestManagerMethods(ut.TestCase):
    def setUp(self):
        if not "HOME" in os.environ:
            home = '.'
        else:
            home = os.environ["HOME"]

        dbDirectory = os.path.join(home, '.ndn')
        self.databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')
                
        if os.path.isfile(self.databaseFilePath):
            os.remove(self.databaseFilePath)
        self.manager = DeviceUserAccessManager()

    def tearDown(self):
        pass

    def test_01_manager_constructor(self):
        print("test")
        if not "HOME" in os.environ:
            home = '.'
        else:
            home = os.environ["HOME"]

        dbDirectory = os.path.join(home, '.ndn')
        self.databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')
        self.manager = DeviceUserAccessManager()
        self.assertTrue(os.path.isfile(self.databaseFilePath), 'fail to create database file')

    def test_02_device_methods(self):
        #create device
        prefixStr = '/home/sensor/LED/1'
        name = Name(prefixStr)
        profile = DeviceProfile(prefix = name)
        location = 'living_room'
        profile.setLocation(location)
        serviceProfileList  = ['/standard/sensor/simple-camera-control/v0', '/standard/sensor/simple-motionsensor-control/v0']
        profile.setServiceProfile(serviceProfileList)
        keyContent = 'this is key content'
        seedName = 'led1'
        seed =  HMACKey( 0, 0 ,keyContent, seedName)
        configurationToken =  HMACKey(0, 0, keyContent) 
  
        commandName1 = 'turn_on'
        commandName2 = 'turn_off' 
        commandList =  [commandName1, commandName2]
        result = self.manager.createDevice(profile, seed, configurationToken, commandList)
        self.assertTrue(result, 'fail to create device')
       
        #getDeviceProfile()
        deviceProfile = self.manager.getDeviceProfile(name)
        self.assertTrue(deviceProfile.getLocation() == location, 'wrong location in device profile ')
        self.assertTrue(deviceProfile.getServiceProfileList() == serviceProfileList, 'wrong service profile list in device profile' )
     
        #getSeed()
        seed = self.manager.getSeed(name)
        self.assertTrue(seed.getName() == seedName, 'wrong seed name')
        
        #getConfigurationToken()
        configurationToken = self.manager.getConfigurationToken(name)
        self.assertTrue(configurationToken.getKey()== keyContent, 'wrong configration token')
       
        #getCommandToken()
        commandToken1 = self.manager.getCommandToken(name, commandName1)
        commandToken2 = self.manager.getCommandToken(name, commandName2)
        commandTokenName1 = name.toUri()+"/"+ commandName1 +"/token/0"
        commandTokenName2 = name.toUri()+"/"+ commandName2 +"/token/0"

        self.assertTrue(commandToken1.getName() == commandTokenName1, 'wrong commandToken')
        self.assertTrue(commandToken2.getName() == commandTokenName2, 'wrong commandToken')
 
        #getCommandsOfDevice()
        commandNameList = self.manager.getCommandsOfDevice(name)
        self.assertTrue(commandName1 in commandNameList, 'command:' + commandName1 + ' not found')
        self.assertTrue(commandName2 in commandNameList, 'command:' + commandName2 + ' not found')

        #getServiceProfilesOfDevice()
        serviceProfileListReturned = self.manager.getServiceProfilesOfDevice(name)
        self.assertTrue(serviceProfileList[0] in serviceProfileListReturned, 'service profile:' + serviceProfileList[0] + ' not found')
        self.assertTrue(serviceProfileList[1] in serviceProfileListReturned, 'service profile:' + serviceProfileList[1] + ' not found')

    def test_03_user_access_methods(self):
        #prerequisite: add device and command
        devicePrefixStr = '/home/sensor/LED/1'
        devicePrefix = Name(devicePrefixStr)
        self.create_a_default_device(devicePrefix)
        
        #add user
        username = 'user1'
        userPrefixBase = '/home'
        userPrefixStr = userPrefixBase + '/' + username
        userPrefix = Name(userPrefixStr)
        hash_ = 'EEADFADSFAGASLGALS'
        salt = 'adfafdwekldsfljcdc'
        type_ = 'guest'    
        result = self.manager.addUser(userPrefix, username, hash_, salt, type_)
        self.assertTrue(result > 0, 'fail to add user')
       
        #add access
        commandName = 'turn_off'
        userDevice = 'laptop'
        keyContent = 'this is key content'
        accessToken =  HMACKey(0, None, keyContent, 'accessToken1')
        result = self.manager.addAccess(devicePrefix, commandName, userPrefix, userDevice, accessToken)
        self.assertTrue(result > 0, 'fail to add acces')

        #get access info 
        accessList = self.manager.getAccessInfo(userPrefix,devicePrefix)
        row = accessList[0]
        self.assertTrue(row[0] == commandName, 'wrong access info: command name')
        self.assertTrue(row[1] == userDevice, 'wrong access info: user device')
        self.assertTrue(row[2].getName() == 'accessToken1', 'wrong access info: access token')

    def create_a_default_device(self, prefixName):
        """
        create a default device with specified device prefix name and with two default commands 'turn_on' and 'turn_off'
        """

        name = prefixName
        profile = DeviceProfile(prefix = name)      
        keyContent = 'this is key content'
        seedName = 'led1'
        seed =  HMACKey( 0, 0 ,keyContent, seedName)
        configurationToken =  HMACKey(0, 0, keyContent)  
        commandName1 = 'turn_on'
        commandName2 = 'turn_off'
        commandList =  [commandName1, commandName2]
        result = self.manager.createDevice(profile, seed, configurationToken, commandList)
        self.assertTrue(result, 'fail to create device')
        
        
if __name__ == '__main__':
    ut.main(verbosity=2)

