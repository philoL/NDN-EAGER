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

import sys
import os
import sqlite3
from device_user_access_storage import DeviceUserAccessStorage
def showDefault(databaseFilePath = None):
    if databaseFilePath == None or databaseFilePath == "":
        if not "HOME" in os.environ:
            home = '.'
        else:
            home = os.environ["HOME"]

        dbDirectory = os.path.join(home, '.ndn')
        if not os.path.exists(dbDirectory):
            os.makedirs(dbDirectory)

        databaseFilePath = os.path.join(dbDirectory, 'ndnhome-controller.db')

        database =  sqlite3.connect(databaseFilePath)
        storage = DeviceUserAccessStorage(databaseFilePath)
        cursor = database.cursor()
        cursor.execute("SELECT id, prefix  FROM Device")
        print 'id:     prefix:                  Commands:                   ServiceProfile:'
        for row in cursor.fetchall():
            commandResult = storage.getCommandsOfDevice(row[0])
            commandStr =''
            for command in commandResult:
                commandStr += command[0] + ';'
            profileResult = storage.getServiceProfilesOfDevice(row[0])
            profileStr=''
            for profile in profileResult:
                profileStr = profile[0] +';'
            print '%d    %s    %s    %s' %(row[0], row[1], commandStr, profileStr ) 
            
        cursor.close()



if len(sys.argv) < 2:
    showDefault()
     
else:
    raise RuntimeError("options is not implemented yet") 
    

