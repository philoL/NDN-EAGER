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
from user_access_storage import UserAccessStorage

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

        cursor = database.cursor()
        cursor.execute("SELECT command_id, user_id, user_device, access_token_name FROM Access")
        print 'command id:  user id:     user_device,     access token name:'
        for row in cursor.fetchall():
            print '%d            %d            %s           %s' %(row[0], row[1], row[2], row[3])
        cursor.close()

if len(sys.argv) < 2:
    showDefault()

else:
    raise RuntimeError("options is not implemented yet")

