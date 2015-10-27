import matplotlib.pyplot as plt
#from matplotlib.font_manager import FontProperties

key_number = [10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,170,180,190,200]

v_ndn_ace = [0.55]*20 
v_acl_hmac =[2.43, 3.84, 7.49, 8.90,10.30,11.71, 13.12, 14.52, 24.93, 26.34,27.74,29.15,30.55,31.96,33.37,34.77,36.18,37.59,38.99,40.40]
v_acl_rsa_object =[11.30,20.76,32.46,41.91,51.37,60.82,70.27,79.37,98.18,107.63,117.09,126.54,135.99,145.45,154.90,164.35,173.80,183.26,192.71,202.16]
v_acl_rsa_raw = [5.95,10.87,18.04,22.96,27.88,32.80,37.73,42.65,56.57,61.49,66.41,71.34,76.26,81.18,86.10,91.02,95.95,100.87,105.79,110.71]

p_ndn_ace = plt.plot(key_number, v_ndn_ace,'ro')
p_acl_hmac = plt.plot(key_number, v_acl_hmac, 'bo')
p_acl_rsa_object = plt.plot(key_number, v_acl_rsa_object, 'go')
p_acl_rsa_raw = plt.plot(key_number, v_acl_rsa_raw, 'yo')

plt.axis([0, 200, 0, 205])


paramValues = key_number
plt.xticks(paramValues)
plt.xlabel('The Number of Command Senders')
plt.ylabel('Memory Usage of Keying Material/ KB')

plt.legend( (p_ndn_ace[0], p_acl_hmac[0], p_acl_rsa_object[0], p_acl_rsa_raw[0]), 
	('NDN-ACE', 'ACL-HMAC', 'ACL-RSA-object', 'ACL-RSA-RAW') ,  loc='upper center')
#,bbox_to_anchor=(0.5, 1.05),
#          ncol=3, fancybox=True, shadow=True)



plt.show()

