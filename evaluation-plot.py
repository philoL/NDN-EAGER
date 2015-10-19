import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties


p1 = plt.plot([10,30,50,70,90,110], [0.55,0.55,0.55,0.55,0.55,0.55] ,'ro')
p2 = plt.plot([10,30,50,70,90,110], [1.61,4.92,7.10,9.30,15.99,18.17], 'bo')
p3 = plt.plot([10,30,50,70,90,110], [2.21,5.87,7.27,8.68,19.09,20.49], 'go')
plt.axis([10, 110, 0, 25])


paramValues = [10,30,50,70,90,110]
plt.xticks(paramValues)
plt.xlabel('The Number of Command Senders')
plt.ylabel('Memory Usage of Keying Material/ KB')

plt.legend( (p1[0], p2[0], p3[0]), ('NDN-ACE', 'ACL-HMAC', 'ACL-RSA') ,  loc='upper center')
#,bbox_to_anchor=(0.5, 1.05),
#          ncol=3, fancybox=True, shadow=True)



plt.show()

