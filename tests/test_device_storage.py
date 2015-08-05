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
from device_storage import DeviceStorage
from device_profile import DeviceProfile
from hmac_key import HMACKey

class TestDeviceStorageMethods(ut.TestCase):
    def setUp(self):
        if not "HOME" in os.environ:
            home = '.'
        else:
            home = os.environ["HOME"]

        dbDirectory = os.path.join(home, '.ndn')
        self.databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')

        if os.path.isfile(self.databaseFilePath):
            os.remove(self.databaseFilePath)
        
        self.storage = DeviceStorage()

    def tearDown(self):
        pass
    
    def test_01_storage_constructor(self):
        
        self.assertTrue(os.path.isfile(self.databaseFilePath), 'fail to create database file')        
        self.assertTrue(self.storage.doesTableExist("Device"), "Device table doesn't exist")  
        self.assertTrue(self.storage.doesTableExist("Command"), "Command table doesn't exist")
        self.assertTrue(self.storage.doesTableExist("ServiceProfile"), "ServiceProfile table doesn't exist") 
        #test constructor with file path HOME/.ndn/homedb 
        home = os.environ["HOME"]
        dir = os.path.join(home, '.ndn')
        dbdir = os.path.join(dir, 'homedb')
        
        if not os.path.exists(dbdir):
                os.makedirs(dbdir)
       
        filePath = os.path.join(dbdir, 'ndnhome-controller.db')
        storage2 = DeviceStorage(filePath)
        self.assertTrue(os.path.isfile(filePath), 'fail to create database file' )
        os.remove(filePath)
    
    def test_02_entry_existence_methods(self):
        # test the existence of non-existed device (prefix = /home/sensor/LED/1)
        prefixStr = '/home/sensor/LED/1'
        name = Name(prefixStr)        
        profile = DeviceProfile(prefix = name)
        keyContent = 'this is key content'
        seed =  HMACKey( 0, 0 ,keyContent, 'led1')
        configurationToken =  HMACKey(0, 0, keyContent)
        result = self.storage.doesDeviceExist(name)
        self.assertFalse(result, "device with prefix '" + prefixStr +  "' shouldn't exist")
        
        #test existence of an existed device 
        self.storage.addDevice(profile, seed, configurationToken)
        result = self.storage.doesDeviceExist(name)
        self.assertTrue(result, "device with prefix '" + prefixStr +"' should exist")
        
        #test existence of a non-existed command
        deviceId = 1 
        commandName = 'turn_on'
        result = self.storage.doesCommandExist(deviceId, commandName)
        self.assertFalse(result, "Command : 'device_id =" + str(deviceId) + ", name = " + commandName + "' shouldn't exist" ) 
       
        #test existence of a existed command
        deviceId = self.storage.getDeviceId(name)
        commandName = 'turn_on'
        commandToken = self.create_a_default_key('turn_on')
        self.storage.addCommand(deviceId, commandName, commandToken)
        result = self.storage.doesCommandExist(deviceId, commandName)
        self.assertTrue(result, "Command : 'device_id =" + str(deviceId) + ", name = " + commandName + "' should exist" )
           
        #test existence of a non-existed service profile
        deviceId = 1
        serviceProfileName = '/standard/sensor/simple-LED-control/v0'
        
        result = self.storage.doesServiceProfileExist(deviceId, serviceProfileName)
        self.assertFalse(result, "service profile : 'device_id =" + str(deviceId) + ", name = " + serviceProfileName + "' shouldn't exist" )

        #test existence of a existed service profile
        deviceId = self.storage.getDeviceId(name)
        serviceProfileName = '/standard/sensor/simple-LED-control/v0'

        self.storage.addServiceProfile(deviceId, serviceProfileName)
        result = self.storage.doesServiceProfileExist(deviceId, serviceProfileName)
        self.assertTrue(result, "service profile : 'device_id =" + str(deviceId) + ", name = " + serviceProfileName + "' should exist" )
 

    def test_03_add_device(self):
        prefixStr = '/home/sensor/LED/1'
        name = Name(prefixStr)
        profile = DeviceProfile(prefix = name)
        keyContent = 'this is key content'
        seed =  HMACKey( 0, 0 ,keyContent, 'led1')
        configurationToken =  HMACKey(0, 0, keyContent)
        
        result = self.storage.addDevice(profile, seed, configurationToken)

        self.assertTrue(result > 0, 'fail to add device entry')             
        self.assertTrue(self.storage.doesDeviceExist(name), "device doesn't exist in table")        
        row = self.storage.getDeviceEntry(name)
        self.assertTrue(row[1] == prefixStr, "column prefix has incorrect value")
        #print row[2:7]
        self.assertTrue(row[2:8] == (None, None, None, None, None, None), "column 2-7 have incorrect values ")
        self.assertTrue(row[8] == 'led1', 'colum seed_name has incorrect values')
        self.assertTrue(row[9:12] == (0,0,keyContent), 'colum seed_sequence or seed_counter has incorrect value')
        self.assertTrue(row[12:] == (keyContent,0,0), 'one or more configuration token columns have incoorect value')
        #try to insert the same device
        result = self.storage.addDevice(profile, seed, configurationToken)
        self.assertTrue(result == 0, 'unexpected result when trying to insert an already existed device')

    def test_04_delete_device(self):
        name = Name('/home/sensor/LED/1')
        profile = DeviceProfile(prefix = name)
        seed =  HMACKey( 0, 0 ,'this is key content', 'led1')
        configurationToken =  HMACKey(0, 0, 'this is key content')
        self.storage.addDevice(profile, seed, configurationToken)
        self.assertTrue(self.storage.doesDeviceExist(name), "device doesn't exist in table")
        result = self.storage.deleteDevice(name)
        #print 'result : %d' %(result)
        self.assertTrue(result == 1, 'fail to delete device')

    def test_05_get_deviceid(self):
        name = Name('/home/sensor/LED/1')
        profile = DeviceProfile(prefix = name)
        seed =  HMACKey( 0, 0 ,'this is key content', 'led1')
        configurationToken =  HMACKey(0, 0, 'this is key content')
        self.storage.addDevice(profile, seed, configurationToken)
        deviceId = self.storage.getDeviceId(name)
        self.assertTrue(deviceId==1, "get a wrong device id")
        
        name2 = Name('/home/sensor/LED/2')
        profile = DeviceProfile(prefix = name2)
        seed =  HMACKey( 0, 0 ,'this is key content', 'led1')
        configurationToken =  HMACKey(0, 0, 'this is key content')
        self.storage.addDevice(profile, seed, configurationToken)
        deviceId2 = self.storage.getDeviceId(name2)
        self.assertTrue(deviceId2 == 2, "get a wrong device id")
     
    def test_06_update_device(self):
        prefixStr = '/home/sensor/LED/1' 
        name = Name(prefixStr)
        self.add_a_default_device(prefixStr)

        #update column prefix of device 
        newPrefixStr = '/home/sensor/LED/2'
        newSeedName = 'led2'
        self.storage.updateOneColumnOfDevice(name, 'seed_name', newSeedName)
        row = self.storage.getDeviceEntry(name)
        self.assertTrue(row[8] == newSeedName, "fail to update column: seed_name")

        self.storage.updateOneColumnOfDevice(name, 'prefix', newPrefixStr) 
        row = self.storage.getDeviceEntry(Name(newPrefixStr))
       
        self.assertTrue(row[1] == newPrefixStr, "fail to update coumn: prefix")     
  
    def test_07_add_command(self):
        prefixStr = '/home/sensor/LED/2'
        name = Name(prefixStr)
        self.add_a_default_device(prefixStr)
        deviceId = self.storage.getDeviceId(name)
        commandName = 'turn_on'
        commandToken = self.create_a_default_key('turn_on')
        self.storage.addCommand(deviceId, commandName, commandToken)        
        result = self.storage.doesCommandExist(deviceId, commandName)
        self.assertTrue(result == True, "fail to add command")

    def test_08_delete_command(self):
        prefixStr1 = 'home/sensor/LED/1'
        name1 = Name(prefixStr1)
        self.add_a_default_device(prefixStr1)     
        deviceId = self.storage.getDeviceId(name1)
        commandName = 'turn_on'
        commandToken = self.create_a_default_key(commandName)
        self.storage.addCommand(deviceId, commandName, commandToken)
        self.assertTrue(self.storage.doesCommandExist(deviceId, commandName), 'before delete, the command should exist')
        self.storage.deleteCommand(deviceId, commandName)
        self.assertFalse(self.storage.doesCommandExist(deviceId, commandName), "after delete, the command shouldn't exist")
        
    def test_09_get_commands_of_device(self):
        #test with an empty table
        deviceId = 2
        result = self.storage.getCommandsOfDevice(deviceId) 
        print result
        self.assertTrue(not result, "there should be no command found")
      
        #test with a device has two commands
        prefixStr = 'home/sensor/LED/1' 
        name = Name(prefixStr)
        self.add_a_default_device(prefixStr)
        deviceId = self.storage.getDeviceId(name)
        commandName = 'turn_on'
        commandName2 = 'turn_off'
        commandToken = self.create_a_default_key(commandName)
        commandToken2 = self.create_a_default_key(commandName2)
        self.storage.addCommand(deviceId, commandName, commandToken)
        self.storage.addCommand(deviceId, commandName2, commandToken)
        result = self.storage.getCommandsOfDevice(deviceId)
        print 'result %s' %(result)
       
    def test_10_add_service_profile(self):
        prefixStr = '/home/sensor/LED/2'
        name = Name(prefixStr)
        self.add_a_default_device(prefixStr)
        deviceId = self.storage.getDeviceId(name)

        serviceProfileName = '/standard/sensor/simple-LED-control/v0'
        self.storage.addServiceProfile(deviceId, serviceProfileName)
        result = self.storage.doesServiceProfileExist(deviceId, serviceProfileName)
        self.assertTrue(result == True, "fail to add service profile")

    def test_11_delete_service_profile(self):
        prefixStr1 = 'home/sensor/LED/1'
        name1 = Name(prefixStr1)
        self.add_a_default_device(prefixStr1)
        deviceId = self.storage.getDeviceId(name1)
        serviceProfileName = '/standard/sensor/simple-LED-control/v0'        

        self.storage.addServiceProfile(deviceId, serviceProfileName)
        self.assertTrue(self.storage.doesServiceProfileExist(deviceId, serviceProfileName), 'before delete, the service profile should exist')
        self.storage.deleteServiceProfile(deviceId, serviceProfileName)
        self.assertFalse(self.storage.doesServiceProfileExist(deviceId, serviceProfileName), "after delete, the service profile shouldn't exist")

    def test_12_get_service_profiles_of_device(self):
        #test with an empty table
        deviceId = 2
        result = self.storage.getServiceProfilesOfDevice(deviceId)
        print result
        self.assertTrue(not result, "there should be no command found")

        #test with a device has two commands
        prefixStr = 'home/sensor/LED/1'
        name = Name(prefixStr)
        self.add_a_default_device(prefixStr)
        deviceId = self.storage.getDeviceId(name)
        serviceProfileName = '/standard/sensor/simple-LED-control/v0'
        serviceProfileName2 = '/standard/sensor/simple-LED-control/v2'
        self.storage.addServiceProfile(deviceId, serviceProfileName)
        self.storage.addServiceProfile(deviceId, serviceProfileName2)
        result = self.storage.getServiceProfilesOfDevice(deviceId)
        print 'result %s' %(result)

    def test_13_get_device_profile_from_device(self):
        #test with a non exisited device prefix
        prefixStr = '/home/sensor/LED/2'
        name = Name(prefixStr)
        deviceProfile = self.storage.getDeviceProfileFromDevice(name)
        self.assertTrue(deviceProfile == None, "no device profile should be return with an non-existed prefix ")
       
        #test with a existed device prefix
        profile = DeviceProfile(prefix = name, location = 'bedroom', category = 'sensors')
        seed = self.create_a_default_key('led1')
        configurationToken = self.create_a_default_key()
        self.storage.addDevice(profile, seed, configurationToken)

        deviceProfile  = self.storage.getDeviceProfileFromDevice(name)
        
        self.assertTrue(deviceProfile.getLocation() == 'bedroom', 'wrong field: location')
        self.assertTrue(deviceProfile.getCategory() == 'sensors', 'wrong field: category')

    def test_14_get_seed_and_get_configuration_token(self):
        #test with a non existed device prefix
        prefixStr = '/home/sensor/LED/2'
        name = Name(prefixStr)
        seed = self.storage.getSeed(name)
        configurationToken = self.storage.getConfigurationToken(name)
        self.assertTrue(seed == None, "no seed should be returned with an non-existed prefix ")
        self.assertTrue(configurationToken == None, "no configuration token should be returned with an non-existed prefix ")
        
        #test with an existed device prefix
        profile= DeviceProfile(prefix = name)
        seed = self.create_a_default_key('led2')
        configurationToken = self.create_a_default_key()
        self.storage.addDevice(profile, seed, configurationToken)
        seed = self.storage.getSeed(name)
        configurationToken = self.storage.getConfigurationToken(name)
        keyContent = 'this is key content'
        self.assertTrue(seed.getKey() == keyContent, 'key content of seed  is incorrect')
        self.assertTrue(configurationToken.getKey() == keyContent, 'key content of configuration token is incorrect')
        self.assertTrue(seed.getName() == 'led2', 'name of seed is incorrect')
        self.assertTrue(configurationToken.getName() == None, 'name of configuration token is incorrect')
  
    def test_15_get_Command_Token(self):
        #test with a non existed command
        deviceId = 5
        commandName = "turn_on"
        commandToken =  self.storage.getCommandToken(deviceId, commandName)
        self.assertTrue(commandToken == None,  'no commandToken should be returned with an non-existed command')
        
        #test with an existed command
        prefixStr = 'home/sensor/LED/1'
        name = Name(prefixStr)
        self.add_a_default_device(prefixStr)
        deviceId = self.storage.getDeviceId(name)
        commandToken = self.create_a_default_key(commandName)
        self.storage.addCommand(deviceId, commandName, commandToken)

        commandTokenReturned =  self.storage.getCommandToken(deviceId, commandName)
        #print commandTokenReturned.getName()
        self.assertTrue(commandTokenReturned.getName() == commandName,  'wrong command token')

    def add_a_default_device(self, prefixStr):
        name = Name(prefixStr)
        profile = DeviceProfile(prefix = name)
        seed = self.create_a_default_key('led1')
        configurationToken = self.create_a_default_key()
        self.storage.addDevice(profile, seed, configurationToken)
    
    def create_a_default_key(self, keyName = None):
        keyContent = 'this is key content'
        seed = HMACKey(0,0, keyContent, keyName)
        return seed
         
if __name__ == '__main__':
    ut.main(verbosity=2)

         
