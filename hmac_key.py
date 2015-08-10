# -*- Mode:python; c-file-style:"gnu"; indent-tabs-mode:nil -*- */
#
# Copyright (C) 2014 Regents of the University of California.
# Author: Weiwei Liu <summerwing10@gmail.com> 
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

class HMACKey(object):
    """
    HMACKey implements the  HMAC symmetric key
    """
    def __init__(self, sequence = None, counter = None, key = None, name = None):
        self._name = name
        self._sequence = sequence
        self._counter = counter
        self._key = key

    def getName(self):
        return self._name
  
    def getSequence(self):
        return self._sequence
 
    def getCounter(self):
        return self._counter
   
    def getKey(self):
        return self._key
        
