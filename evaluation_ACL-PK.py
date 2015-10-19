from  pympler import asizeof




def generate_RSA(bits=2048):
    '''
    Generate an RSA keypair with an exponent of 65537 in PEM format
    param: bits The key length in bits
    Return private key and public key
    '''
    from Crypto.PublicKey import RSA 
    new_key = RSA.generate(bits, e=65537) 
    public_key = new_key.publickey().exportKey("PEM") 
    private_key = new_key.exportKey("PEM") 
    return private_key, public_key


private_key , public_key = generate_RSA()


#private_key = private_key.split("\n")[1:-1]
#public_key =public_key.split("\n")[1]

#print private_key 
#print public_key



for each in [10,30,50,70,90,110]:
	print each

	keys = {}
	#keys["/UA-cs-718/device/light/1/private-key"] = private_key

	for i in range(each):
	    
	    key_name = "/UA-cs-718/device/switch/"+str(i)+"/key/0"
	    keys[key_name] = public_key



	print len(keys.keys())
	print asizeof.asized(keys).format()