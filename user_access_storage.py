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
UserAccessStorage implements a basic storage of users and access 
"""

import os
import sqlite3
from pyndn import Name
from device_profile import DeviceProfile
from hmac_key import HMACKey

INIT_USER_TABLE = ["""
CREATE TABLE IF NOT EXISTS
  User(
      id                             INTEGER,
      prefix                         BLOB NOT NULL UNIQUE,
      username                      BLOB NOT NULL UNIQUE,
      hash                           BLOB NOT NULL,
      salt                           BLOB NOT NULL,
      type                           BLOB NOT NULL,
      
      PRIMARY KEY (id)
  );
"""]

INIT_ACCESS_TABLE = ["""
CREATE TABLE IF NOT EXISTS
  Access(
      id                             INTEGER,
      command_id                     INTEGER,
      user_id                        INTEGER,
      user_device                    BLOB NOT NULL,
      access_token_name              BLOB,
      access_token_sequence          INTEGER NOT NULL,
      access_token                   BLOB NOT NULL,
      
      PRIMARY KEY (id)
      FOREIGN KEY(command_id) REFERENCES Command(id)
      FOREIGN KEY(user_id) REFERENCES User(id)
  );
"""]

class UserAccessStorage(object):
    """
    Create a new UserAccessStorage to work with an SQLite file.
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
      
        #Check if the User table exists
        cursor = self._database.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE TYPE ='table' and NAME = 'User'")
        if cursor.fetchone() == None:
            #no device table exists, create one
            for command in INIT_USER_TABLE:
                self._database.execute(command)
        cursor.close()

        #Check if the Access table exists
        cursor = self._database.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE TYPE ='table' and NAME = 'Access'")
        if cursor.fetchone() == None:
            #no device table exists, create one
            for command in INIT_ACCESS_TABLE:
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
    
    def doesUserExistByPrefix(self, prefix):
        """
        Check if the specified user already exists.
       
        :param Name prefix: the prefix of user
        :return True if the user exists, otherwise False
        :rtype: bool
        """
        result = False
               
        cursor = self._database.cursor()
        cursor.execute("SELECT count(*) FROM User WHERE prefix =?", (prefix.toUri(),))
        (count,) = cursor.fetchone()
        if count > 0:
            result = True
            #print 'device with %s is founnd, count %d' %(prefix, count)

        cursor.close()
        return result

    def doesUserExistByUsername(self, username):
        """
        Check if the specified user already exists.
       
        :param str username: the username of user
        :return True if the user exists, otherwise False
        :rtype: bool
        """
        result = False

        cursor = self._database.cursor()
        cursor.execute("SELECT count(*) FROM User WHERE username =?", (username,))
        (count,) = cursor.fetchone()
        if count > 0:
            result = True
            #print 'device with %s is founnd, count %d' %(prefix, count)

        cursor.close()
        return result


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
        data = ( prefix.toUri(), username, hash_, salt, type_)
        
        #check if there already exists a user with the same prefix, if yes return 0 
        if self.doesUserExistByPrefix(prefix):
            return 0

        #check if there already exists a user with the same username, if yes return -1
        if self.doesUserExistByUsername(username):
            return -1
        
        #add user to dababase
        insertUser = (
            "INSERT INTO User(prefix, username, hash, salt, type)"
            "VALUES(?,?,?,?,?)"
        )
        cursor = self._database.cursor()
        cursor.execute(insertUser, data)
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
        return result
   
    def getUserId(self, prefix):
        """
        get the user id of a specified user
        :param Name prefix: the prefix of the user
        :return id of the user, 0 if the user doesn't exist
        :rtype: INTEGER
        """
        if not self.doesUserExistByPrefix(prefix):
            return 0
        cursor = self._database.cursor()
        operation = "SELECT id FROM User WHERE prefix=?"
        cursor.execute(operation, (prefix.toUri(),))
        result = cursor.fetchone()
        userId = result[0]
        self._database.commit()
        cursor.close()
        return userId

    def updateUser(self, prefix, hash_, salt, type_):
        """
        update specifided user
        :param Name prefix 
        :param hash_ 
        :param salt
        :param str type_: the type of the user
        :return id of the user if successful, 0 if user not found
        :rtype int
        """
        if not self.doesUserExistByPrefix(prefix):
            return 0

        updateUser = "UPDATE User Set hash=?, salt =?, type=? WHERE prefix=?"
        cursor = self._database.cursor()
        cursor.execute(updateUser, (hash_, salt, type_, prefix.toUri()))
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
 
    def getUserEntry(self, prefix):
        """
        get the specified User entry
        :param Name prefix: the user prefix
        :return the corresponding row of the device
        :rtype: str
        """
        cursor = self._database.cursor()
        cursor.execute("SELECT * FROM User WHERE prefix =?", (prefix.toUri(),))
        row = cursor.fetchone()
        cursor.close()
        return row

    def deleteUser(self, prefix):
        """
        delete specified user.
        :param Name prefix: The user prefix
        :return: 1 if successful, 0 if no device to delete, otherwise -1.
        :rtype: INTEGER 
        """
        result = -1
        if not self.doesUserExistByPrefix(prefix):
            return 0
        cursor = self._database.cursor()
        deleteUser = "DELETE FROM User WHERE prefix=?"
        cursor.execute(deleteUser, (prefix.toUri(),))
        self._database.commit()
        cursor.close()
        return 1

    def doesAccessExist(self, commandId, userId, userDevice=None):
        """
        check if the specified access already exists.
       
        :param int userId: user id
        :param int commandId: command id
        :param str userdevice: user device name
        :return True if the access exists, otherwise False
        :rtype: bool
        """
        result = False
        
        cursor = self._database.cursor()
        if userDevice == None:
            operation = "SELECT count(*) FROM Access WHERE user_id =? AND command_id=? "
            data = (userId, commandId)
        else: 
            operation = "SELECT count(*) FROM Access WHERE user_id =? AND command_id=? AND user_device=?" 
            data = (userId, commandId, userDevice)
        cursor.execute(operation, data)

        (count,) = cursor.fetchone()
        if count > 0:
            result = True
        cursor.close()
        return result
    
    def addAccess(self, commandId, userId, userDevice, accessToken):
        """ 
        Add a new access to the Access table, do nothing if the access already exists
        
        :param int commandId: the command id 
        :param int userId: the user id
        :param int userDevice: the user device
        :param HMACKey accessToken: the access token
        :return the access id if it's added successfully, 0 if the access already exists, otherwise -1
        :rtype: int
        """
        result = -1
        data = (commandId,
               userId,
               userDevice,
               accessToken.getName(),
               accessToken.getSequence(),
               accessToken.getKey()
               )

        #check if the access already exists, if yes return 0
        if self.doesAccessExist(commandId, userId, userDevice):
            return 0

        insertAccess = (
            "INSERT INTO Access(command_id, user_id, user_device, access_token_name, access_token_sequence, access_token)"
            "VALUES(?,?,?,?,?,?)"
        )
        cursor = self._database.cursor()
        cursor.execute(insertAccess, data)
        self._database.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def deleteAccess(self, commandId, userId):
        """
        delete specified accesses.
        :param int commandId: The command id
        :param int userId: the user id
        :return: 1 if successful, 0 if no access to delete.
        :rtype: int
        """
        if not self.doesAccessExist(userId, userId):
            return 0
        cursor = self._database.cursor()
        deleteAccess = "DELETE FROM Access WHERE command_id=? AND user_id=?"
        cursor.execute(deleteAccess, (commandId, userId))
        self._database.commit()
        cursor.close()
        return 1

    def getCommandsOfUser(self, userId):
        """
        get all the commands to which the specified user has access.
        :param int userId: user id
        :return command id list if any commands exist, otherwise None
        """
        cursor = self._database.cursor()
        operation = "SELECT DISTINCT command_id FROM Access WHERE user_id=?"
        cursor.execute(operation,(userId,))
        result = cursor.fetchall()
        cursor.close()
   
        commandIdList = []
        if result == None:
           return commandIdList
        else:
           for row in result:
               commandIdList.append(row[0])

        return commandIdList

    def getAccessToken(self,commandId, userId, userDevice):
        """
        get access token of a specified access 
        :param int commandId: command id
        :param int userId: user id  
        :param str userDevice: user device
        :return access token if access exists, otherwise None
        :rtype HMACKey
        """
        operation = "SELECT access_token_sequence, access_token, access_token_name FROM Access WHERE command_id = ? AND user_id = ? AND user_device=?"
        cursor = self._database.cursor()
        cursor.execute(operation, (commandId, userId, userDevice))
        result = cursor.fetchone()
        cursor.close()

        if result == None:
            return None
        else:
            accessToken = HMACKey(sequence = result[0], key = result[1], name = result[2])
        return accessToken
   
    def getUserDevices(self, commandId, userId):
        """
        get user devices given commandi id and user id
        :param int commandId: command id
        :param int userId: user id  
        :return a list of user device
        :rtype list
        """
        operation = "SELECT user_device from Access WHERE command_id=? AND user_id=?"
        cursor = self._database.cursor()
        cursor.execute(operation,(commandId, userId))
        result = cursor.fetchall()
        cursor.close()

        userDeviceList = []        
        if result == None: 
            return userDeviceList

        for row in result:
            userDeviceList.append(row[0])

        return userDeviceList

