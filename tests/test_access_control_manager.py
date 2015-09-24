


if __name__ == '__main__':
    a = AccessControlManager()
    seed = sha256("seed").digest()

    seed = HMACKey(0,0,seed,"seedName")
    interest = Interest(Name("/home/sensor/LED/T12321/turnOn/1/2"))
    ctn = "/home/sensor/LED/T12321/turnOn/token/2"
    atn = ctn+"/user/Teng/07"
    print ctn
    print atn
    ct = hmac.new(seed.getKey(),ctn,sha256).digest()
    at = hmac.new(ct,atn,sha256).digest()

    h = HMACKey(0,0,at,atn)
    
    a.signInterestWithHMACKey(interest,h)

    print a.verifyCommandInterestWithSeed(interest,seed)
