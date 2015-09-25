import ftplib
from .. import edgar_config as ec
import pysec.util.edgar_utilies as eu
import os
import Queue

class FTP_Connector :

    def __init__(self):

        self.server   = ec.FTP_IP
        self.user     = 'anonymous'
        self.password = 'anonymous'

        while True:
            try :
                self.connection = ftplib.FTP(ec.FTP_IP)
                self.connection.login(self.user,self.password)
            except EOFError:
                continue
            break

        

    def get_sec_XRBL(self,cik,acc):
        
        location = { 'short_cik' : eu.long_to_short_cik(cik),
                     'acc'       : eu.remove_dashes_acc(acc)} # waste of time
        
        self.connection.cwd(ec.FTP_DIR % location)
        ls = self.connection.nlst()
        
        xml_file = None
        for i in ls:
            if ec.FTP_REGEX.search(i) is not None:
                xml_file = i; break;
        
        if xml_file is None:
            raise Exception("Can not find .xml file in FTP server on cik %s" % d['short_cik'])
        
        filename = eu.add_dashes_acc(acc) + ec.XBRL_ZIP_EXT
        
        
        os.chdir(ec.DOWNLOAD_FLDR)
        if os.path.isfile(xml_file):
            return ec.DOWNLOAD_FLDR + xml_file
            
        f = open(ec.DOWNLOAD_FLDR + filename, 'wb')
        self.connection.retrbinary("RETR " + filename, f.write)
        f.close()

        if os.system('unzip -o -j %s %s -d %s > /dev/null' % (filename,xml_file,ec.DOWNLOAD_FLDR)):
            raise Exception("Unable to unzip %s" % filename)
        
        if not os.path.isfile(xml_file):
            raise Exception("Could not find %s in %s" % (xml_file,ec.DOWNLOAD_FLDR))
        
        return ec.DOWNLOAD_FLDR + xml_file
    
class FTP_Pool: # not extensible, just use with FTP_Connector class

    def __init__(self,pool_size = 4):
        self.proxy_pool = Queue.Queue() # FIFO instance
        for i in xrange(pool_size):
            instance = FTP_Connector()
            self.proxy_pool.put(instance)

    def get(self,cik,acc,q):
        proxy  = self.proxy_pool.get()       # Get some object in FIFO
        result = proxy.get_sec_XRBL(cik,acc) # open FTP to get data
        self.proxy_pool.put(proxy)           # Put object back in FIFO
        q.put((acc,result))                  # Put final result into another Q
        
