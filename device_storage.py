# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Teng Liang <philoliang2011@gmail.com> 
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
DeviceStorage implements a basic storage of devices and corresponding commands
"""

import os
import sqlite3
from pyndn import Name
from device_profile import DeviceProfile
from hmac_key import HMACKey

INIT_DEVICE_TABLE = ["""
CREATE TABLE IF NOT EXISTS
  Device(
      id                             INTEGER,
      prefix                         BLOB NOT NULL UNIQUE,
      location                       BLOB,
      category                       BLOB,
      type                           BLOB,
      model                          BLOB,
      serial_number                  BLOB,
      manufacturer                   BLOB,
      seed_name                      BLOB NOT NULL,
      seed_sequence                  INTEGER NOT NULL,
      seed_counter                   INTEGER NOT NULL,
      seed                           BLOB NOT NULL,
      configuration_token            BLOB NOT NULL,
      configuration_token_sequence   INTEGER NOT NULL,
      configuration_token_counter    INTEGER NOT NULL,
      
      PRIMARY KEY (id)
  );
"""]

INIT_COMMAND_TABLE = ["""
CREATE TABLE IF NOT EXISTS
  Command(
      id                            INTEGER,
      device_id                     INTEGER NOT NULL,
      name                          BLOB NOT NULL,
      command_token_name            BLOB NOT NULL,
      command_token_sequence        INTEGER NOT NULL,
      command_token_counter         INTEGER NOT NULL,
      command_token                 BLOB NOT NULL,
      
      PRIMARY KEY(id)
      FOREIGN KEY(device_id) REFERENCES Device(id)
  );
"""]

INIT_SERVICE_PROFILE_TABLE = ["""
CREATE TABLE IF NOT EXISTS
  ServiceProfile(
      id                            INTEGER,
      device_id                     INTEGER NOT NULL,
      name                          BLOB NOT NULL,
      
      PRIMARY KEY(id)
      FOREIGN KEY(device_id) REFERENCES Device(id)
  );
"""]

class DeviceStorage(object):
    """
    Create a new DeviceUserStorage to work with an SQLite file.
    :param str databaseFilePath: (optional) The path of the SQLite file. If ommitted, use the default path.
    """
    def __init__(self, databaseFilePath = None):
        if databaseFilePath == None or databaseFilePath == "":
            if not "HOME" in os.environ:
                home = '.'
            else:
                home = os.environ["HOME"]
            
            dbDirectory = os.path.join(home, '.ndn')
            if not os.path.exists(dbDirectory):
                os.makedirs(dbDirectory)

            databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')

        self._database =  sqlite3.connect(databaseFilePath)
        
        #Check if the Device table exists
        cursor = self._database.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE TYPE ='table' and NAME = 'Device'")
        if cursor.fetchone() == None:
            #no device table exists, create one
            for command in INIT_DEVICE_TABLE:
                self._database.execute(command)
        cursor.close()
        
        #Check if the Command table exists
        cursor = self._database.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE TYPE ='table' and NAME = 'Command'")
        if cursor.fetchone() == None:
            #no command table exists, create one
            for command in INIT_COMMAND_TABLE:
                self._database.execute(command)
        cursor.close()

        #Check if the ServiceProfile table exists
        cursor = self._database.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE TYPE ='table' and NAME = 'ServiceProfile'")
        if cursor.fetchone() == None:
            #no ServiceProfile table exists, create one
            for command in INIT_SERVICE_PROFILE_TABLE:
                self._database.execute(command)
        cursor.close()

        self._database.commit()
   
    def doesTableExist(self, tableName):
        """
         check if table exists
         :param str tableName
         :return True if exists, otherwise False
        """
        selectOperation = "SELECT name FROM sqlite_master WHERE TYPE='table' and NAME='" + tableName +"'"
        #print selectOperation
        cursor = self._database.cursor()
        cursor.execute(selectOperation)
        if cursor.fetchone() == None:
            result = False
        else: 
            result = True
        cursor.close()
        return result

    def doesDeviceExist(self, prefix):
        """
        Check if the specified device already exists.
       
        :param Name prefix: the prefix of device
        :return True if the device exists, otherwise False
        :rtype: bool
        """
        result = False
        #print prefix        
        cursor = self._database.cursor()
        cursor.execute("SELECT count(*) FROM Device WHERE prefix =?", (prefix.toUri(),))
        (count,) = cursor.fetchone()
        if count > 0:
            result = True
            #print 'device with %s is founnd, count %d' %(prefix, count)

        cursor.close()
        return result

    def addDevice(self, deviceProfile, seed, configurationToken):
        """ 
        Add a new device to the Device table, do nothing if the device already exists
        
        :param DeviceProfile devicePorfile: the deviceProfile of the device
        :param Key seed: the seed of the device
        :param Key configurationToken: the configurationToken of the device
        :return the device id if it's added successfully, 0 if the device already exists, otherwise -1
        :rtype: INTEGER
        """
        result = -1
        data = (deviceProfile.getPrefix().toUri(),
               deviceProfile.getLocation(),
               deviceProfile.getCategory(),
               deviceProfile.getType(),
               deviceProfile.getModel(),
               deviceProfile.getManufacturer(),
               deviceProfile.getSerialNumber(),
               seed.getName(),
               seed.getSequence(),
               seed.getCounter(),
               seed.getKey(),
               configurationToken.getKey(),
               configurationToken.getSequence(),
               configurationToken.getCounter()
              )     

        #check if the device already exists, if yes return 0
        prefixName = deviceProfile.getPrefix()
        if self.doesDeviceExist(prefixName):
            return 0

        insertDevice = (
            "INSERT INTO Device(prefix, location, category, type, model, manufacturer, serial_number, seed_name, seed_sequence, seed_counter,seed, configuration_token, configuration_token_sequence, configuration_token_counter)"
            "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        )
        cursor = self._database.cursor()
        cursor.execute(insertDevice, data)
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def getDeviceProfileFromDevice(self, prefix):
        """
        get the specified device profile
        :param Name prefix: the device prefix
        :return device profile of the device if exists, otherwise return None
        :rtype: DeviceProfile
        """   
        operation = (
            "Select location, category, type, model, manufacturer, serial_number FROM Device "
            "WHERE prefix = ?"
        )
    
        cursor = self._database.cursor() 
        cursor.execute(operation, (prefix.toUri(),))
        result = cursor.fetchone() 
        cursor.close()
        # print result
        if result == None:
            return None
        else:               
            deviceProfile = DeviceProfile(prefix)
            deviceProfile.setLocation(result[0])
            deviceProfile.setCategory(result[1])
            deviceProfile.setType(result[2])
            deviceProfile.setModel(result[3])
            deviceProfile.setManufacturer(result[4])
            deviceProfile.setSerialNumber(result[5])
        
        return deviceProfile
               
    def getSeed(self, prefix):
        """
        get the seed of the specified device        
        :param Name prefix: the device prefix
        :return seed of the device if exists, otherwise return None
        :rtype: HMACKey

        """
        operation = (
            "Select seed_name, seed_sequence, seed_counter, seed FROM Device "
            "WHERE prefix = ?"
        )

        cursor = self._database.cursor()
        cursor.execute(operation, (prefix.toUri(),))
        result = cursor.fetchone()
        cursor.close()
        #print result
        if result == None:
            return None
        else:
            seed = HMACKey(result[1], result[2], result[3], result[0]) 
        return seed

        # raise RuntimeError("getSeed is not implemented")

    def getConfigurationToken(self, prefix):
        """
        get the seed of the specified device        
        :param Name prefix: the device prefix
        :return seed of the device if exists, otherwise return None
        :rtype: HMACKey

        """
        operation = (
            "Select configuration_token_sequence, configuration_token_counter, configuration_token FROM Device "
            "WHERE prefix = ?"
        )

        cursor = self._database.cursor()
        cursor.execute(operation, (prefix.toUri(),))
        result = cursor.fetchone()
        cursor.close()
        #print result
        if result == None:
            return None
        else:
            configurationToken = HMACKey(result[0], result[1], result[2])
        return configurationToken
        # raise RuntimeError("getConfigurationToken is not implemented")

    def getDeviceEntry(self, prefix):
        """
        get the specified device entry
        :param Name prefix: the device prefix
        :return '' return the corresponding row of the device
        :rtype: str
        """        
        cursor = self._database.cursor()
        cursor.execute("SELECT * FROM Device WHERE prefix =?", (prefix.toUri(),))
        row = cursor.fetchone()
        cursor.close()
        return row

    def deleteDevice(self, prefix):
        """
        delete specified device.
        :param Name prefix: The device prefix
        :return: 1 if successful, 0 if no device to delete, otherwise -1.
        :rtype: INTEGER	
        """
        result = -1
        if not self.doesDeviceExist(prefix):
            return 0
        cursor = self._database.cursor()
        deleteDevice = "DELETE FROM Device WHERE prefix=?"
        cursor.execute(deleteDevice, (prefix.toUri(),))
        self._database.commit()
        cursor.close()
        return 1
   
    def getDeviceId(self, prefix):
        """
        get the device id of some specified device
        :param Name prefix: the device prefix
        :return id of the device, 0 if the device doesn't exist
        :rtype: INTEGER
        """
        if not self.doesDeviceExist(prefix):
            return 0
        cursor = self._database.cursor()
        operation = "SELECT id FROM Device WHERE prefix=?"
        cursor.execute(operation, (prefix.toUri(),))
        result = cursor.fetchone()
        deviceId = result[0]
        self._database.commit()
        cursor.close()
        return deviceId
    
    def updateDevice(self, prefix, newDeviceProfile = None , newSeed = None , newcConfigurationToken = None ):
        """
        update specifided device 
        :param Name prefix 
        :param DeviceProfile newDeviceProfile
        :param HMACKey newSeed
        :param newConfigurationToken
        :return id of the device if successful, 0 if device not found, otherwise -1
        :rtype int
        """
        raise RuntimeError("getConfigurationToken is not implemented")

    def updateOneColumnOfDevice(self, prefix, columnName, newColumnValue):
        """
        update the value of a specified column of a specified device
        :param Name prefix: the device prefix
        :param str columnName: column to be updated 
        :param newColumnValue: new column value
        :return id of the device if successful. 0 if device not found, otherwise -1
        :rtype int
        """
        result  = -1
        if not self.doesDeviceExist(prefix):
            return 0
        
        updateDevice = "UPDATE Device Set " + columnName + "=? WHERE prefix=?"
        #print updateDevice       
        cursor = self._database.cursor()
        #print  newColumnValue
        cursor.execute(updateDevice, (newColumnValue,prefix.toUri()))
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def doesCommandExist(self, deviceId, commandName):
        """
        check if the specified command already exists.
       
        :param Integer device_id: the device id
        :return True if the command exists, otherwise False
        :rtype: bool
        """
        result = False

        cursor = self._database.cursor()
        cursor.execute("SELECT count(*) FROM Command WHERE device_id =? AND name = ?", (deviceId, commandName))
        (count,) = cursor.fetchone()
        if count > 0:
            result = True
        
        cursor.close()
        return result
    
    def addCommand(self, deviceId, name, commandToken):
        """ 
        Add a new command to the Command table, do nothing if the device already exists
        
        :param int deviceId: the device id to which the command belongs to
        :param str name: the command name
        :param HMACKey commandToken: the command token
        :return the command id if it's added successfully, 0 if the command already exists, otherwise -1
        :rtype: int
        """
        result = -1
        data = (deviceId,
               name,
               commandToken.getName(),
               commandToken.getSequence(),
               commandToken.getCounter(),
               commandToken.getKey()
               )

        #check if the command already exists, if yes return 0
        if self.doesCommandExist(deviceId, name):
            return 0

        insertCommand = (
            "INSERT INTO Command(device_id, name, command_token_name, command_token_sequence, command_token_counter, command_token)"
            "VALUES(?,?,?,?,?,?)"
        )
        cursor = self._database.cursor()
        cursor.execute(insertCommand, data)
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
        return result
    
    def deleteCommand(self, deviceId, name = None):
        """
        delete specified commands.
        :param str name: The command name, if None, delete all commands of the device
        :param int deviceId: device id of the command
        :return: 1 if successful, 0 if no command to delete, otherwise -1.
        :rtype: int
        """
        result = -1
        if not name == None: 
            if not self.doesCommandExist(deviceId, name):
                return 0
            cursor = self._database.cursor()
            deleteCommand = "DELETE FROM Command WHERE device_id=? AND name=?"
            cursor.execute(deleteCommand, (deviceId, name))
            self._database.commit()
            cursor.close()
            return 1
        else: 
            selectOperation = "SELECT count(*) FROM Command WHERE deviceId=?"
            cursor = self._database.cursor()
            cursor.execute(selectOperation, (deviceId,))
            (count,) = cursor.fetchone()
            if not count > 0:
                return 0
            deleteCommand = "DELETE FROM Command WHERE deviceId=?"
            cursor.execute(deleteCommand, (deviceId))
            self._database.commit()
            cursor.close()
            return 1
        
        return result
      
    def getCommandsOfDevice(self, deviceId):
        """
        get all the commands of a specified device
        :param int deviceId: device id of the command
        :return command name list if any commands exist, otherwise None

        """
        operation = "SELECT name FROM Command WHERE device_id = ?"
        #operation2 = "SELECT count(*) FROM Command WHERE device_id = ? "
        cursor = self._database.cursor()
        #cursor.execute(operation2,(deviceId,))
        #(count,) = cursor.fetchone

        #if not count > 0:
            #return None
        cursor.execute(operation, (deviceId,))
        result = cursor.fetchall()                    
        #print result
        commandList = []
        if result == None:
           return commandList 
        else:  
           for row in result:
               commandList.append(row[0]) 
    
        return commandList

    def getCommandToken(self, deviceId, commandName):
        """
        get command token of a specified command 
        :param int deviceId: device id of the command
        :param str commandName: device name of the command
        :return command token if command existsm, otherwise None
        :rtype HMACKey
        """
        operation = "SELECT command_token_sequence, command_token_counter,command_token, command_token_name FROM Command WHERE device_id = ? AND name = ?"
        cursor = self._database.cursor()
        cursor.execute(operation, (deviceId, commandName))
        result = cursor.fetchone()
        if result == None:
            return None
        else:
            commandToken = HMACKey(result[0], result[1], result[2], result[3])
        return commandToken
  
    def doesServiceProfileExist(self, deviceId, serviceProfileName):
        """
        check if the specified service profile already exists.
       
        :param Integer device_id: the device id
        :param str serviceProfileName: name of the service profile 
        :return True if the service profile exists, otherwise False
        :rtype: bool
        """
        result = False

        cursor = self._database.cursor()
        cursor.execute("SELECT count(*) FROM ServiceProfile WHERE device_id =? AND name = ?", (deviceId, serviceProfileName))
        (count,) = cursor.fetchone()
        if count > 0:
            result = True

        cursor.close()
        return result

    def addServiceProfile(self, deviceId, name):
        """ 
        Add a new command to the ServiceProfile table, do nothing if the device already exists
        
        :param int deviceId: the device id to which the command belongs to
        :param str name: the service profile name
        :return the service profile id if it's added successfully, 0 if the service profile already exists, otherwise -1
        :rtype: int
        """
        result = -1
        data = (deviceId,
               name,
               )

        #check if the service profile already exists, if yes return 0
        if self.doesServiceProfileExist(deviceId, name):
            return 0

        insertCommand = (
            "INSERT INTO ServiceProfile(device_id, name)"
            "VALUES(?,?)"
        )
        cursor = self._database.cursor()
        cursor.execute(insertCommand, data)
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def deleteServiceProfile(self, deviceId, name = None):
        """
        delete specified service profile.
        :param str name: The command name, if None, delete all profiless of the device
        :param int deviceId: device id 
        :return: 1 if successful, 0 if no service profile to delete, otherwise -1.
        :rtype: int
        """
        result = -1
        if not name == None:
            if not self.doesServiceProfileExist(deviceId, name):
                return 0
            cursor = self._database.cursor()
            deleteProfile = "DELETE FROM ServiceProfile WHERE device_id=? AND name=?"
            cursor.execute(deleteProfile, (deviceId, name))
            self._database.commit()
            cursor.close()
            return 1
        else:
            selectOperation = "SELECT count(*) FROM ServiceProfile WHERE deviceId=?"
            cursor = self._database.cursor()
            cursor.execute(selectOperation, (deviceId,))
            (count,) = cursor.fetchone()
            if not count > 0:
                return 0
            deleteProfile = "DELETE FROM ServiceProfile WHERE deviceId=?"
            cursor.execute(deleteProfile, (deviceId))
            self._database.commit()
            cursor.close()
            return 1

        return result

    def getServiceProfilesOfDevice(self, deviceId):
        """
        get all the service profiles of a specified device
        :param int deviceId: device id of the command
        :return service profiles name list if any service profiles exist, otherwise None
        """
        operation = "SELECT name FROM ServiceProfile WHERE device_id = ?"
        cursor = self._database.cursor()
        cursor.execute(operation, (deviceId,))
        result = cursor.fetchall()
        #print result
        serviceProfileList = []
        if not result == None:
            for row in result:
                serviceProfileList.append(row[0])
        return serviceProfileList


