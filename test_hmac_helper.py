from hmac_helper import HmacHelper
from pyndn import Data, KeyLocatorType, Interest, Name
import unittest as ut
from pyndn.encoding import WireFormat

def dumpData(data):
    result = []
    result.append(dump("name:", data.getName().toUri()))
    if len(data.getContent()) > 0:
        result.append(dump("content (raw):", str(data.getContent())))
        result.append(dump("content (hex):", data.getContent().toHex()))
    else:
        result.append(dump("content: <empty>"))
    if not data.getMetaInfo().getType() == ContentType.BLOB:
        result.append(dump("metaInfo.type:",
             "LINK" if data.getMetaInfo().getType() == ContentType.LINK
             else "KEY" if data.getMetaInfo().getType() == ContentType.KEY
             else "unknown"))
    result.append(dump("metaInfo.freshnessPeriod (milliseconds):",
         data.getMetaInfo().getFreshnessPeriod()
         if data.getMetaInfo().getFreshnessPeriod() >= 0 else "<none>"))
    result.append(dump("metaInfo.finalBlockId:",
         data.getMetaInfo().getFinalBlockId().toEscapedString()
         if len(data.getMetaInfo().getFinalBlockId().getValue()) > 0
         else "<none>"))
    signature = data.getSignature()
    if type(signature) is Sha256WithRsaSignature:
        result.append(dump("signature.signature:",
             "<none>" if len(signature.getSignature()) == 0
                      else signature.getSignature().toHex()))
        if signature.getKeyLocator().getType() is not None:
            if (signature.getKeyLocator().getType() ==
                KeyLocatorType.KEY_LOCATOR_DIGEST):
                result.append(dump("signature.keyLocator: KeyLocatorDigest:",
                     signature.getKeyLocator().getKeyData().toHex()))
            elif signature.getKeyLocator().getType() == KeyLocatorType.KEYNAME:
                result.append(dump("signature.keyLocator: KeyName:",
                     signature.getKeyLocator().getKeyName().toUri()))
            else:
                result.append(dump("signature.keyLocator: <unrecognized KeyLocatorType"))
        else:
            result.append(dump("signature.keyLocator: <none>"))
    return result

def dump(*list):
    result = ""
    for element in list:
        result += (element if type(element) is str else repr(element)) + " "
    print(result)

class hmacHelperTest(ut.TestCase):
	
    def setUp(self):
		self.raw_key = "seed"
		self.raw_key_name = "/home/seed/s1"
		self.h = HmacHelper(raw_key = self.raw_key)
    
    def test_sign_verify_interest(self):
    	freshInterest = Interest(Name("/home/controller"))
    	self.h.signInterest(freshInterest, self.raw_key_name)
         
        s = freshInterest.extractInterestSignature()
        k = s.getKeyLocator().getName().toUri()
        result = self.h.verifyInterest(freshInterest)        
        self.assertEqual(result, True, 'verifiedInterest does not match original interest')

    def test_sign_verify_data(self):
        freshData = Data(Name("/ndn/abc"))
        freshData.setContent("SUCCESS!")
        freshData.getMetaInfo().setFreshnessPeriod(5000.0)
        freshData.getMetaInfo().setFinalBlockId(Name("/%00%09")[0])

       
        self.h.signData(freshInterest, self.raw_key_name)
         
        result = self.h.verifyInterest(freshInterest)        
        self.assertEqual(result, True, 'verifiedInterest does not match original interest')



if __name__ =='__main__':
    ut.main()
