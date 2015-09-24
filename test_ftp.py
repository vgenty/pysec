import Queue
import threading
from pysec.util import ftp_connector

class FTPPool:
    def __init__(self,pool_size = 3):
        self.proxy_pool = Queue.Queue() # FIFO instance
        for i in xrange(pool_size):
            instance = ftp_connector.FTP_Connector()
            self.proxy_pool.put(instance)

    def get(self,cik,acc):
        proxy  = self.proxy_pool.get()  # Get some object in FIFO
        result = proxy.get_sec_XRBL(cik,acc) # open FTP to get data
        self.proxy_pool.put(proxy)
        
        return result
    
pool = FTPPool(5)

def get_file(cik,acc):
    print pool.get(cik,acc)
    
j = ['0000005272-15-000014',
     '0000005272-15-000006',
     '0000005272-14-000013',
     '0000005272-14-000010',
     '0000005272-14-000007',
     '0001047469-13-010141',
     '0001047469-13-008075',
     '0001047469-13-005458',
     '0001047469-12-009952',
     '0001047469-12-007690']

def test():
    for i in j:
        t = threading.Thread(target = get_file,
                             args=('5272',i))
        t.start()
        

test()
                             
