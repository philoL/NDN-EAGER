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
This module gives an example of LED instance
"""

from device import Device
from device_profile import DeviceProfile
from pyndn import Data
import json
import io
import picamera
import time
import base64
import sys
from pyndn.meta_info import MetaInfo
from pyndn.util.blob import Blob

class Camera(Device):

    def __init__(self,configFileName=None):
        super(Camera, self).__init__(configFileName)

        self._identity = "/home/security/camera/0"
        self._deviceProfile = DeviceProfile(category = "security", type_= "camera", serialNumber = "0")
        self.addCommands(['capture'])
        
        self.camera = picamera.PiCamera()
        self.camera.resolution = (640, 480)
        self.stream = io.BytesIO()
        self.segmentSize = 7000
        self.segmentNumber = 1
        self.segmentList = []
        self.dataList = []

    def capture(self, interest, transport):
        
       # print("capture cmd received start processing")
        interestName = interest.getName()

        if (interestName.size() >= 7):
            #right format 

            segmentIndex = interestName.get(6).toSegment()
           # print "request segmentIndex : ",segmentIndex

            if segmentIndex == 0:
               # print("a new picture")
                #request a new picture
                self.stream = io.BytesIO()
                self.stream.flush()
                self.segmentList = []
                self.dataList = []

                self.camera.capture(self.stream, 'jpeg')
                #print("photo caputred in stream")
                imageBytes = self.stream.getvalue()
                print ("imageBytes %d" % len(imageBytes)) 
                
                #segmentation
                self.segmentNumber = len(imageBytes)/(self.segmentSize+1)+1
                print("segmentNumber: %d" % self.segmentNumber)

                for i in range(self.segmentNumber):
                    startIndex = i*self.segmentSize
                    
                    if (i != self.segmentNumber -1):
                        segBytes = imageBytes[startIndex:(startIndex+self.segmentSize)]
                    else:
                        segBytes = imageBytes[startIndex:]

                    #self.segmentList.append(segBytes)

                    newName = interestName.getPrefix(-1).appendSegment(i)
                    #print newName.toUri()

                    data = Data(newName)
                    metaInfo = MetaInfo()
                    metaInfo.setFinalBlockId(Blob.fromRawStr(str(self.segmentNumber-1)))
                    data.setMetaInfo(metaInfo)
                    #data.setContent(Blob.fromRawStr(self.segmentList[i]))
                    data.setContent(Blob.fromRawStr(segBytes))
                    self.dataList.append(data)
                                         

                self.sendData(self.dataList[0], transport, sign=False)
            else:   
                self.sendData(self.dataList[segmentIndex], transport, sign=False)
        #print("Receved capture cmd. Sent the segment %i." % (segmentIndex))
    
  

if __name__ == "__main__":
    camera = Camera()
    camera.start()
