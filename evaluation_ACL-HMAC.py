from  pympler import asizeof
from hashlib import sha256




for each in [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]:

	keys = {}  
	for i in range(each):
	    
	    key_name = "/UA-cs-718/device/switch/"+str(i)+"/key/0"
	    keys[key_name] = sha256(key_name).digest()



	print len(keys.keys())
	print asizeof.asized(keys).format()

    