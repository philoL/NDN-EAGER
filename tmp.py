f = open("tmp.txt","r")

for each in f:

    if len(each) > 5:

        a = each.split(" ")
    
        for i in a:
 
            if 'size' in i:
 
                t = i[5:]
 
                print "%.2f" % (float(t)/1024.0)

f.close()