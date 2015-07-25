from device_profile import DeviceProfile

def readProfile(profile):
    print '   prefix: ', profile.getPrefix()
    print '   location: ', profile.getLocation()
    print '   manufacturer: ', profile.getManufacturer()
    print '   category: ', profile.getCategory()
    print '   type: ', profile.getType()
    print '   serial number: ', profile.getSerialNumber()
    print '   service profile list:', profile.getServiceProfileList()
    print '   metadata', profile.getMetadata()

def test():
    print 'starting to test device_profile.py'
    print "initilize with category ='sensors', serialNumer = 'T9000000'..."
    profile = DeviceProfile(category = 'sensors', serialNumber = 'T9000000')

    print 'read profile...'
    readProfile(profile)
    
    print "set prefix to '/home/sensor/LED/23'..."
    profile.setPrefix('/home/sensor/LED/23')

    print "set location to 'Alice's bedroom'..."
    profile.setLocation('Alice\'s bedroom')
   
    print "set manufacturer to 'Intel'..."
    profile.setManufacturer('Intel')

    print "set type to 'LED'..."
    profile.setType('LED')
  
    print "set serial number to 'T9273659'..."
    profile.setSerialNumber('T9273659')

    print "add a service profile '/standard/sensor/simple-LED-control/v0'..."
    profile.addServiceProfile('/standard/sensor/simple-LED-control/v0')

    print 'read profile...'
    readProfile(profile)   

    print "add sevice profiles ['/standard/sensor/simple-camera-control/v0', '/standard/sensor/simple-motionsensor-control/v0']..."
    profile.addServiceProfile(['/standard/sensor/simple-camera-control/v0', '/standard/sensor/simple-motionsensor-control/v0'])
    
    print 'read profile...'
    readProfile(profile)

    print "set service profile to ['/standard/sensor/simple-camera-control/v0']... "
    profile.setServiceProfile(['/standard/sensor/simple-camera-control/v0'])

    print 'read profile...'
    readProfile(profile)

    print "add metadata 'name'... "
    profile.addMetadata('name')

    print 'read profile...'
    readProfile(profile)
 
    print "add metadata ['status', 'id']"
    profile.addMetadata(['status', 'id'])

    print 'read profile...'
    readProfile(profile)
    
    print "test 'print profile'..."
    print profile
    
    print "Unit tests: passed"

if __name__ =='__main__':
    test()
    
