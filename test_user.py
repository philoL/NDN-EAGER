from device_user_access_manager import DeviceUserAccessManager
from pyndn import Name
from hashlib import sha256
import time
import json
from pyndn import Name, Face, Interest, Data
from pyndn.key_locator import KeyLocator, KeyLocatorType
from hmac_helper import HmacHelper 
from hmac_key import HMACKey
import hmac 
from hashlib import sha256
from device_profile import  DeviceProfile
import sys
from pyndn.security import KeyChain
from base_node import BaseNode
from pyndn.security import SecurityException
from pyndn.util import Blob
from device_user_access_manager import DeviceUserAccessManager
from access_control_manager import AccessControlManager

try:
    # Use builtin asyncio on Python 3.4+, or Tulip on Python 3.3
    import asyncio
except ImportError:
    # Use Trollius on Python <= 3.2
    import trollius as asyncio
from pyndn import Name
# We must explicitly import from threadsafe_face. The pyndn module doesn't
# automatically load it since asyncio is optional.
from pyndn.threadsafe_face import ThreadsafeFace


def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)


def register():
    while True:
        username = raw_input('New username: ')
        if not len(username)>0:
            print("Username can't be blank")
            continue
        else:
            break
    while True:
        password = raw_input("New password: ")
        if not len(password)>0:
            print("Username can't be blank")
            continue
        else:
            break
     
    print("Creating account...")


    DUAManager = DeviceUserAccessManager()
    prefix = Name("/home/user/"+username)
    hash_ = password
    salt = "default"
    type_ = "USER"
          

    result = DUAManager.addUser(prefix,username,hash_,salt,type_)
    if (result):
        print("Succsess")
    else:
        print("Error") 

    
class Counter(object):
    """
    Counter counts the number of calls to the onData or onTimeout callbacks.
    Create a Counter to call loop.stop() after maxCallbackCount calls to
    onData or onTimeout.
    """
    def __init__(self, loop, maxCallbackCount):
        self._loop = loop
        self._maxCallbackCount = maxCallbackCount
        self._callbackCount = 0
        self._accessControlManager = AccessControlManager()

    def onData(self, interest, data):
        dump("Got data packet with name", data.getName().toUri())
        # Use join to convert each byte to chr.
        dump(data.getContent().toRawStr())

        self._callbackCount += 1
        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()

    def onTimeout(self, interest):
        dump("Time out for interest", interest.getName().toUri())

        self._callbackCount += 1
        if self._callbackCount >= self._maxCallbackCount:
            self._loop.stop()

def login():
    
    loop = asyncio.get_event_loop()
    #face = ThreadsafeFace(loop, "localhost")
    face = Face("localhost")
    # Counter will stop the ioService after callbacks for all expressInterest.
    counter = Counter(loop, 3)

    while True:
        username = raw_input('Login username: ')
        if not len(username)>0:
            print("Username can't be blank")
            continue
        else:
            break
    while True:
        password = raw_input("Login password: ")
        if not len(password)>0:
            print("Username can't be blank")
            continue
        else:
            break
        
    userHMACKey = HMACKey(0,0,password,"userHMACKey")
    
    interestName = Name("/home/controller/login/"+username)
    interest = Interest(interestName)    

    a = AccessControlManager()
    a.signInterestWithHMACKey(interest,userHMACKey)
    dump("Express interst :",interest.toUri())
    face.expressInterest(interest,counter.onData,counter.onTimeout)
    while counter._callbackCount < 1:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(2)

    face.shutdown()

def deviceListRequest():
    
    loop = asyncio.get_event_loop()
    #face = ThreadsafeFace(loop, "localhost")
    face = Face("localhost")
    # Counter will stop the ioService after callbacks for all expressInterest.
    counter = Counter(loop, 3)

    while True:
        username = raw_input('Login username: ')
        if not len(username)>0:
            print("Username can't be blank")
            continue
        else:
            break
    while True:
        password = raw_input("Login password: ")
        if not len(password)>0:
            print("Username can't be blank")
            continue
        else:
            break
        
    userHMACKey = HMACKey(0,0,password,"userHMACKey")
    
    interestName = Name("/home/controller/deviceList/user/"+username)
    interest = Interest(interestName)    

    a = AccessControlManager()
    a.signInterestWithHMACKey(interest,userHMACKey)
    dump("Express interst :",interest.toUri())
    face.expressInterest(interest,counter.onData,counter.onTimeout)
    while counter._callbackCount < 1:
        face.processEvents()
        # We need to sleep for a few milliseconds so we don't use 100% of the CPU.
        time.sleep(2)

    face.shutdown()


 


def delete():
    while True:
        username = raw_input("Username to delete:")
        if not len(username)>0:
            print("Username can't be blank")
            continue
        else:
            break
    DUAManager = DeviceUserAccessManager()
     
    prefix = Name("/home/user/"+username)
    result = DUAManager.deleteUser(prefix) 
    
    if (result):
        print("Succsess")
    else:
        print("Error")

if __name__ == "__main__":
   
    while(1):
        option = raw_input("\nPlease select one of the options:\n0.Exit\n1.User registration\n2.User deletion\n3.User login\n4.Send a device list request\n")
        if option == "1":
            register()
        elif option =="2":
            delete()
        elif option == "0":
            exit(1)
        elif option =="3":
            login()
        elif option =="4":
            deviceListRequest()
