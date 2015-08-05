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
from pyndn.name import Name
from device_profile import DeviceProfile
from device_storage import DeviceStorage

class DeviceUserAccessManager(object):
    """
    Create a new DeviceUserAccessManager
    """
    def __init__(self, databaseFilePath = None):
        deviceUserAccessStorage = DeviceStorage(databaseFilePath)
        self._deviceUserAccessStorage = deviceUserAccessStorage
    
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
        deviceId =  self._deviceUserAccessStorage.addDevice(deviceProfile, seed, configurationToken)  
        if deviceId == 0:
           raise RuntimeError("device already exists in database") 
           return result
        elif deviceId == -1:
           raise RuntimeError("error occured during adding device into database") 
           return result
        
        #add service profile
        serviceProfileList = deviceProfile.getServiceProfileList()
        for serviceProfileName in serviceProfileList:
            serviceProfileId = self._deviceUserAccessStorage.addServiceProfile(deviceId, serviceProfileName)
            if serviceProfileId == 0:
                raise RuntimeError("service profile: " + serviceProfileName + " already exists in database")
                return result
            elif serviceProfileId == -1:
                raise RuntimeError("error occured during adding service profile :" + serviceProfileName)
                return result
        #add command
        for commandTuple in commandList:
            commandId = self._deviceUserAccessStorage.addCommand(deviceId, commandTuple[0], commandTuple[1])
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
        deviceProfile = self._deviceUserAccessStorage.getDeviceProfileFromDevice(prefix)
        if deviceProfile == None:
            return deviceProfile
        else:
            # get device Id 
            deviceId = self._deviceUserAccessStorage.getDeviceId(deviceProfile.getPrefix())
            if deviceId == 0:
                raise RuntimeError("device doesn't exist")
             
            serviceProfileList = self._deviceUserAccessStorage.getServiceProfilesOfDevice(deviceId)
            deviceProfile.setServiceProfile(serviceProfileList)
       
        return deviceProfile

    def getSeed(self, prefix):
        """
        get seed of a specified device
        :param Name prefix: the device prefix
        :return seed of the device if exists, otherwise return None
        :rtype: SymmetricKey
        """
        return self._deviceUserAccessStorage.getSeed(prefix)

    def getConfigurationToken(self, prefix):
        """
        get configuration token of a specified device
        :param Name prefix: the device prefix
        :return seed of the device if exists, otherwise return None
        :rtype: SymmetricKey
        """
        return self._deviceUserAccessStorage.getConfigurationToken(prefix)

    def getCommandToken(self, prefix, commandName):
        """
        get command token of a specified command 
        :param Name prefix: the device prefix 
        :param str commandName: device name of the command
        :return command token if command existsm, otherwise None
        :rtype SymmetricKey
        """
        deviceId = self._deviceUserAccessStorage.getDeviceId(prefix)
        if deviceId == 0:
            return None
        return self._deviceUserAccessStorage.getCommandToken(deviceId, commandName)

    def getCommandsOfDevice(self, prefix):
        """
        get all the commands of a specified device
        :param Name prefix: the device prefix
        :return command name list if any commands exist, otherwise None
        """
        deviceId = self._deviceUserAccessStorage.getDeviceId(prefix)
        if deviceId == 0:
            return None
        return self._deviceUserAccessStorage.getCommandsOfDevice(deviceId)
    
    def getServiceProfilesOfDevice(self, prefix):
        """
        get all the service profiles of a specified device
        :param Name prefix: the device prefix
        :return service profiles name list if any service profiles exist, otherwise None
        """
        deviceId = self._deviceUserAccessStorage.getDeviceId(prefix)
        if deviceId == 0:
            return None
        return self._deviceUserAccessStorage.getServiceProfilesOfDevice(deviceId)
    
