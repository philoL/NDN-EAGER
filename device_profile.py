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
This module defines the DeviceProfile class with holds descriptors of device
"""

class DeviceProfile(object):   
    
    def __init__(self, prefix = None, location = None, manufacturer = None, category = None, type_ = None, model = None, serialNumber = None, serviceProfileList = None):
        '''initialize device profile.'''
        self._prefix = prefix
        self._location = location
        self._manufacturer = manufacturer
        self._category = category
        self._type =  type_
        self._model = model
        self._serialNumber = serialNumber
        if serviceProfileList is None:
            self._serviceProfileList = []
        else:
            self._serviceProfileList = serviceProfileList
        self._metadata = ['prefix', 'location', 'manufacturer', 'category', 'type', 'model', 'serialNumber', 'serviceProfileList']
 
    def __str__(self):
        info ='prefix: '+ self._prefix + '\nlocation: '+ self._location + '\nmanufacturer: ' + self._manufacturer + '\ncategory: ' + self._category + '\ntype: ' + self._type + '\nserial number: ' + self._serialNumber + '\nservice profile list: '
        info += ', '.join(self._serviceProfileList)
        info += '\nmetadata: ' 
        info += ', '.join(self._metadata)
        return info
    
    def getPrefix(self):
        '''get device prefix from profile'''
        return self._prefix

    def getLocation(self):
        '''get device location from profile'''
        return self._location

    def getManufacturer(self):
        '''get device manufacturer from profile'''
        return self._manufacturer

    def getCategory(self):
        '''get device category from profile'''
        return self._category

    def getType(self):
        '''get device type from profile'''
        return self._type
   
    def getModel(self):
        '''get device model from profile'''
        return self._model

    def getSerialNumber(self):
        '''get device serial number from profile'''
        return self._serialNumber

    def getServiceProfileList(self):
        '''get the service profile list that the device support'''
        return self._serviceProfileList
  
    def getMetadata(self):
        '''get metadata from profile'''
        return self._metadata

    def setPrefix(self, prefix):
        '''set device prefix from profile'''
        self._prefix = prefix

    def setLocation(self, location):
        '''set device location from profile'''
        self._location = location

    def setManufacturer(self, manufacturer):
        '''set device manufacturer from profile'''
        self._manufacturer = manufacturer

    def setCategory(self, category):
        '''set device category from profile'''
        self._category = category

    def setType(self, type_):
        '''set device type from profile'''
        self._type = type_

    def setModel(self, model):
        '''set device model from profile'''
        self._model = model

    def setSerialNumber(self, serialNumber):
        '''set device serial number from profile'''
        self._serialNumber = serialNumber

    def setServiceProfile(self, serviceProfileList):
        '''set the service profile list that the device support'''
        self._serviceProfileList = serviceProfileList

    def addServiceProfile(self, newServiceProfile):
        '''
        add one or several service profiles to the service profile list.
        :param str/list _serviceProfile: a service profile or several profiles in the form of a list
        '''
        if isinstance(newServiceProfile, str):
            self._serviceProfileList.append(newServiceProfile)
        elif type(newServiceProfile) is list:
            self._serviceProfileList += newServiceProfile

    def addMetadata(self, newMetadata):
        '''
        add device one or several attributes to metadata.
        :param str/list _newMetadata: new attributes to be added
        '''
        if isinstance(newMetadata, str):
            self._metadata.append(newMetadata)
        elif type(newMetadata) is list:
            self._metadata += newMetadata 
