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
from user_access_storage import UserAccessStorage
from device_profile import DeviceProfile
from hmac_key import HMACKey

class TestUserAccessStorageMethods(ut.TestCase):
    def setUp(self):
        if not "HOME" in os.environ:
            home = '.'
        else:
            home = os.environ["HOME"]

        dbDirectory = os.path.join(home, '.ndn')
        self.databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')

        if os.path.isfile(self.databaseFilePath):
            os.remove(self.databaseFilePath)
        
        self.storage = UserAccessStorage()

    def tearDown(self):
        pass
    
    def test_01_storage_constructor(self):
        
        self.assertTrue(os.path.isfile(self.databaseFilePath), 'fail to create database file')        
        self.assertTrue(self.storage.doesTableExist("User"), "Device table doesn't exist")  
        self.assertTrue(self.storage.doesTableExist("Access"), "Command table doesn't exist")
        
        #test constructor with file path HOME/.ndn/homedb 
        home = os.environ["HOME"]
        dir = os.path.join(home, '.ndn')
        dbdir = os.path.join(dir, 'homedb')
        
        if not os.path.exists(dbdir):
                os.makedirs(dbdir)
       
        filePath = os.path.join(dbdir, 'ndnhome-controller.db')
        storage2 = UserAccessStorage(filePath)
        self.assertTrue(os.path.isfile(filePath), 'fail to create database file' )
        os.remove(filePath)
   
    def test_02_entry_existence_methods(self):
        # test the existence of non-existed user (prefix = /home/weiwei)
        username = 'weiwei'
        prefixBase = '/home'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)                
        result1 = self.storage.doesUserExistByPrefix(prefixName)
        result2 = self.storage.doesUserExistByUsername(username)
        self.assertFalse(result1, "user with prefix '" + prefixStr +  "' shouldn't exist")
        self.assertFalse(result2, "user with username '" + username + "' shouldn't exist")

        #test existence of an existed user
        self.add_a_default_user(username)  
        result1 = self.storage.doesUserExistByPrefix(prefixName)
        result2 = self.storage.doesUserExistByUsername(username)

        self.assertTrue(result1, "user with prefix '" + prefixStr +  "' should exist")
        self.assertTrue(result2, "user with username '" + username + "' should exist")

        #test the existence of a non-existed access 
        commandId = 1
        userId = 1 
        result = self.storage.doesAccessExist(commandId, userId)
        self.assertFalse(result, "access shouldn't exist with a empty Access table")

        #test the exitence of an existed access
        accessToken = self.create_a_default_access_token('user1_command1')
        self.storage.addAccess(1,1, 'laptop', accessToken)
        result = self.storage.doesAccessExist(commandId, userId)
        self.assertTrue(result, "access should exist")

    def test_03_add_user(self):
        username = 'weiwei'
        prefixBase = '/home'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)
        hash_ = 'EEADFADSFAGASLGALS'
        salt = 'adfafdwekldsfljcdc'
        type_ = 'guest'

        result = self.storage.addUser(prefixName, username, hash_, salt, type_)

        self.assertTrue(result > 0, 'fail to add user')             
        self.assertTrue(self.storage.doesUserExistByPrefix(prefixName), "user doesn't exist in table")        
        row = self.storage.getUserEntry(prefixName)

        self.assertTrue(row[1] == prefixStr, "column prefix has incorrect value")
        self.assertTrue(row[2] == username, "column username has incorrect value ")
        self.assertTrue(row[3] == hash_, 'colum hash has incorrect value')
        self.assertTrue(row[4] == salt, 'colum salt has incorrect value')
        self.assertTrue(row[5] == type_, 'column type_ has incoorect value')
        
        #try to insert the same device
        result = self.storage.addUser(prefixName, username, hash_, salt, type_)
        self.assertTrue(result == 0, 'unexpected result when trying to insert an already existed user')

    def test_04_delete_user(self):
        username = 'user1'
        self.add_a_default_user(username)
        prefixBase = '/home'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)
       
        self.assertTrue(self.storage.doesUserExistByPrefix(prefixName), "user doesn't exist in table")
        result = self.storage.deleteUser(prefixName)       
        self.assertTrue(result == 1, 'fail to delete device')

    def test_05_get_userid(self):
        username = 'user1'
        self.add_a_default_user(username) 
        prefixBase = '/home'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)

        userId = self.storage.getUserId(prefixName)
        self.assertTrue(userId==1, "get a wrong user id")
        
        username = 'user2'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)
        self.add_a_default_user(username)

        userId = self.storage.getUserId(prefixName)
        self.assertTrue(userId==2, "get a wrong user id")

    def test_06_update_user(self):
        username = 'user1'
        self.add_a_default_user(username)
        prefixBase = '/home'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)

        #update hash_ salt, type_ value of user 
        newHash = 'NNNMMHGFGKUOIPRT'
        newSalt = 'kjkjfioewprwerke'
        newType = 'user'
        self.storage.updateUser(prefixName, newHash, newSalt, newType)
        row = self.storage.getUserEntry(prefixName)
        self.assertTrue(row[3] == newHash, "fail to update column: hash")
        self.assertTrue(row[4] == newSalt, "fail to update column: salt")
        self.assertTrue(row[5] == newType, "fail to update column: type")

    def test_07_add_access(self):
        username = 'user1'
        self.add_a_default_user(username)

        accessToken = self.create_a_default_access_token('user1_command1')
        self.storage.addAccess(1,1, 'laptop', accessToken)        
        result = self.storage.doesAccessExist(1, 1)
        self.assertTrue(result == True, "fail to add command")

    def test_08_delete_access(self):
        username = 'user1'
        self.add_a_default_user(username)

        accessToken = self.create_a_default_access_token('user1_command1')
        self.storage.addAccess(1,1, 'laptop', accessToken) 

        self.assertTrue(self.storage.doesAccessExist(1, 1), 'before delete, the command should exist')
        self.storage.deleteAccess(1, 1)
        self.assertFalse(self.storage.doesAccessExist(1, 1), "after delete, the command shouldn't exist")

    def test_09_get_commands_of_user(self):        
        accessToken = self.create_a_default_access_token('token1')
        self.storage.addAccess(1,1, 'laptop', accessToken)
        self.storage.addAccess(1,1, 'desktop', accessToken)
        self.storage.addAccess(2,1,'laptop', accessToken)
        self.storage.addAccess(2,1, 'desktop', accessToken)
        result = self.storage.getCommandsOfUser(1)
        self.assertTrue(result == [1,2], 'wrong command list returned')

    def test_10_get_access_token(self):
        accessTokenName1 =  'accessToken1'
        accessTokenName2 = 'accessToken2'
        accessToken1 = self.create_a_default_access_token(accessTokenName1)
        accessToken2 = self.create_a_default_access_token(accessTokenName2)
        userDevice1 = 'laptop'
        userDevice2 = 'desktop'
        accessId1 = self.storage.addAccess(1,1, userDevice1, accessToken1)
        accessId2 = self.storage.addAccess(1,1, userDevice2, accessToken2)
        
        if accessId1 <= 0 or accessId2 <= 0:
            raise RuntimeError('fail to add access') 
        result1 = self.storage.getAccessToken(1,1, userDevice1)
        result2 = self.storage.getAccessToken(1,1, userDevice2)
        if result1 == None or result2 == None:
            self.assertTrue(False, 'no access returned')
        self.assertTrue(result1.getName() == accessTokenName1, 'wrong access token returned')
        self.assertTrue(result2.getName() == accessTokenName2, 'wrong access token returned')
    
    def test_11_get_user_hash(self):
        username = 'user123'
        self.add_a_default_user(username) 
        prefix = Name("/home/"+username)

        hash_ = self.storage.getUserHash(prefix)
        self.assertTrue(hash_ == 'EEADFADSFAGASLGALS', 'wrong hash returned')       
 

    def add_a_default_user(self, username):
        prefixBase = '/home'
        prefixStr =prefixBase +'/' + username
        prefixName = Name(prefixStr)
        hash_ = 'EEADFADSFAGASLGALS'
        salt = 'adfafdwekldsfljcdc'
        type_ = 'guest'

        self.storage.addUser(prefixName, username, hash_, salt, type_)

    def create_a_default_access_token(self, keyName = None):
        keyContent = 'this is key content'
        accessToken = HMACKey(sequence = 0, key = keyContent, name = keyName)
        return accessToken
         
if __name__ == '__main__':
    ut.main(verbosity=2)
 
