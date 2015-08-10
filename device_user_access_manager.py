# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014-2015 Regents of the University of California.
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
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# A copy of the GNU Lesser General Public License is in the file COPYING.

"""
This module defines the DeviceUserAccessManager class which is the interface of
operations related to identity, keys, and certificates.
"""

import sys
import hmac
from hashlib import sha256
from pyndn.name import Name
from device_profile import DeviceProfile
from device_storage import DeviceStorage
from hmac_key import HMACKey
from user_access_storage import UserAccessStorage

class DeviceUserAccessManager(object):
    """
    Create a new DeviceUserAccessManager
    """
    def __init__(self, databaseFilePath = None):
        deviceStorage = DeviceStorage(databaseFilePath)
        self._deviceStorage = deviceStorage
        userAccessStorage  = UserAccessStorage(databaseFilePath)
        self._userAccessStorage =  userAccessStorage 
 
    def createDevice(self, deviceProfile, seed, configurationToken, commandList = None):
        """
        Create a device in the database, including it's corresponding commands and serrvice profiles
        @param DeviceProfile deviceProfile: the device profile
        @param SymmetricKey seed: the seed of the device
        @param SymmetricKey configurationToken: the configuration Token of the device
        @param list commandList: the command list of the device, must have following structure: each element in the list should be a two-tuple (commandName, commandToken), the commandName should be a string, and commandToken should be a SymmetricKey. Here is an example of a valid commandList : [('turn_on', commandToken1), ('turn_off', commandToken2)]
        return True if succeed, otherwise False
        """
        result = False

        #add device
        deviceId =  self._deviceStorage.addDevice(deviceProfile, seed, configurationToken)  
        if deviceId == 0:
           raise RuntimeError("device already exists in database") 
           return result
        elif deviceId == -1:
           raise RuntimeError("error occured during adding device into database") 
           return result
        
        #add service profile
        serviceProfileList = deviceProfile.getServiceProfileList()
        for serviceProfileName in serviceProfileList:
            serviceProfileId = self._deviceStorage.addServiceProfile(deviceId, serviceProfileName)
            if serviceProfileId == 0:
                raise RuntimeError("service profile: " + serviceProfileName + " already exists in database")
                return result
            elif serviceProfileId == -1:
                raise RuntimeError("error occured during adding service profile :" + serviceProfileName)
                return result

        #add command
        for command in commandList:
            #generate command token,firstt generate command token name
            prefix = deviceProfile.getPrefix()
            commandTokenName = prefix.toUri()+"/"+command+"/token/0"
            commandTokenKey = hmac.new(seed.getKey(), commandTokenName,sha256).digest()
            commandToken = HMACKey(0,0,commandTokenKey,commandTokenName)

            commandId = self._deviceStorage.addCommand(deviceId, command, commandToken)
            if commandId == 0:
                raise RuntimeError("command: " + commandTuple[0] + " already exists in database")
                return result
            elif commandId == -1:
                raise RuntimeError("error occured during adding command:" +commandTuple[0])
                return result
        result = True
        return result

    def getDeviceProfile(self, prefix):
        """
        get device profile of a specified device
        :param Name prefix: the device prefix
        :return device profile of the device if exists, otherwise return None
        :rtype: DeviceProfile
        """
        deviceProfile = self._deviceStorage.getDeviceProfileFromDevice(prefix)
        if deviceProfile == None:
            return deviceProfile
        else:
            # get device Id 
            deviceId = self._deviceStorage.getDeviceId(deviceProfile.getPrefix())
            if deviceId == 0:
                raise RuntimeError("device doesn't exist")
             
            serviceProfileList = self._deviceStorage.getServiceProfilesOfDevice(deviceId)
            deviceProfile.setServiceProfile(serviceProfileList)
       
        return deviceProfile

    def getSeed(self, prefix):
        """
        get seed of a specified device
        :param Name prefix: the device prefix
        :return seed of the device if exists, otherwise return None
        :rtype: SymmetricKey
        """
        return self._deviceStorage.getSeed(prefix)

    def getConfigurationToken(self, prefix):
        """
        get configuration token of a specified device
        :param Name prefix: the device prefix
        :return seed of the device if exists, otherwise return None
        :rtype: SymmetricKey
        """
        return self._deviceStorage.getConfigurationToken(prefix)

    def getCommandToken(self, prefix, commandName):
        """
        get command token of a specified command 
        :param Name prefix: the device prefix 
        :param str commandName: device name of the command
        :return command token if command existsm, otherwise None
        :rtype SymmetricKey
        """
        deviceId = self._deviceStorage.getDeviceId(prefix)
        if deviceId == 0:
            return None
        return self._deviceStorage.getCommandToken(deviceId, commandName)

    def getCommandsOfDevice(self, prefix):
        """
        get all the commands of a specified device
        :param Name prefix: the device prefix
        :return command name list if any commands exist, otherwise None
        """
        deviceId = self._deviceStorage.getDeviceId(prefix)
        if deviceId == 0:
            return None
        return self._deviceStorage.getCommandsOfDevice(deviceId)
    
    def getServiceProfilesOfDevice(self, prefix):
        """
        get all the service profiles of a specified device
        :param Name prefix: the device prefix
        :return service profiles name list if any service profiles exist, otherwise None
        """
        deviceId = self._deviceStorage.getDeviceId(prefix)
        if deviceId == 0:
            return None
        return self._deviceStorage.getServiceProfilesOfDevice(deviceId)
 
    def addUser(self, prefix, username, hash_, salt, type_):
        """ 
        Add a new user to User table, do nothing if the user already exists
        
        :param Name prefix: the prefix of the user
        :param str username: username
        :param hash_: 
        :param salt: 
        :param str type: the type of user, either guest or user
        :return the user id if it's added successfully, 0 if prefix conflict exists, -1 if username conflict exists
        :rtype: INTEGER
        """
        return self._userAccessStorage.addUser(prefix, username, hash_, salt, type_)

    def addAccess(self, devicePrefix, commandName, userPrefix, userDevice, accessToken):
        """ 
        Add a new access to the Access table, do nothing if the access already exists
        :param Name devicePrefix: the device prefix
        :param str command name : the command name
        :param Name userPrefix: the user prefix
        :param int userDevice: the user device
        :param HMACKey accessToken: the access token
        :return the access id if it's added successfully, 0 if the access already exists, otherwise -1
        :rtype: int
        """
        #get device Id
        deviceId = self._deviceStorage.getDeviceId(devicePrefix)
        if deviceId == 0:
            print 1
            return -1
        
        #get command id
        commandId = self._deviceStorage.getCommandId(deviceId, commandName)
        if commandId == 0:
            print 2
            return -1

        #get user id 
        userId = self._userAccessStorage.getUserId(userPrefix)
        if userId ==0:
            print 3
            return -1 
       
        return self._userAccessStorage.addAccess(commandId, userId, userDevice, accessToken)
  
    def getAccessInfo(self, userPrefix, devicePrefix):
        """
        get all aceess info for pair(user, device)
        :param Name userPrefix: the prefix of user
        :param Name devicePrefix: the prefix of device
        :return a list of tuples of form (str commandName,str userDevice, HmacKey accessToken). e.g. [('turn_on','laptop'. AccessToken1), ('turn_off','laptop' AccessToken2)], return None if no such access exists     
        :rtype list 
        """
        #get device Id
        deviceId = self._deviceStorage.getDeviceId(devicePrefix)
        
        #get user Id 
        userId = self._userAccessStorage.getUserId(userPrefix)
        
        if userId <= 0 or deviceId <= 0:
            #either user or device doesn't exist in table 
            return None
     
       #get command id list of device 
        commandIdList = self._deviceStorage.getCommandIdsOfDevice(deviceId)
        if commandIdList == []:
           return None
       
        accessList =[]
        for commandId in commandIdList:
            doesExist = self._userAccessStorage.doesAccessExist(commandId, userId)
            if doesExist: 
                commandName = self._deviceStorage.getCommandNameFromId(commandId)
                userDeviceList =  self._userAccessStorage.getUserDevices(commandId, userId)
                for userDevice in userDeviceList:
                     accessToken = self._userAccessStorage.getAccessToken(commandId, userId, userDevice)
                     accessTuple  =  (commandName, userDevice, accessToken)
                     accessList.append(accessTuple)
        
        return accessList
