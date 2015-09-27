import Queue
import threading
import pysec.util.edgar_utilies as eu
import sym_to_ciks

from pysec.util import ftp_utilities

T = 'AET'

TCKR = sym_to_ciks.sym_to_ciks[T]

TCKR_df = eu.get_acc_table({'cik' : eu.short_to_long_cik(TCKR),
                            'qk'  : 'q'})

pool = ftp_utilities.FTP_Pool(4)
q    = Queue.Queue() # Return queue

def get_xbrl_file(cik,acc,q):
    pool.get(cik,acc,q) # Race condition failure

th = []
for i in TCKR_df.Acc.values:
    t = threading.Thread(target = get_xbrl_file,
                         args=(str(TCKR),i,q)) # Send queue as parameters to safeguard blocking
    t.start()
    th.append(t)

for t in th:
    t.join()

# add extra column to dataframe that just has "fileloc"
TCKR_df['Fileloc'] = ''

# Pull out of FIFO, put back into dataframe one by one
# will be in Quene in random order (or some function of filesize/avg internet speed)
while not q.empty():
    ret = q.get()
    TCKR_df.loc[TCKR_df['Acc'] == ret[0],'Fileloc'] = ret[1]
    

print TCKR_df
