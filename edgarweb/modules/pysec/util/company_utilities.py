import Queue
import threading

import pysec.util.edgar_utilies as eu
import pysec.util.ftp_utilities as fu

import sym_to_ciks as stc
# T = 'AET'

# TCKR = sym_to_ciks.sym_to_ciks[T]

def get_company_df(ticker,qk):

    # keep them separate for now, in the future we return them
    # in the same dataframe ordered by filing date (Q1-Q4 per year whatever)
    if qk not in ['q','k']:
        raise Exception("qk parameter is not q or k...")

    cik = stc.sym_to_ciks[ticker] # hopefully it's in there i don't even fucking check
    
    TCKR_df = eu.get_acc_table({'cik' : eu.short_to_long_cik(cik),
                                'qk'  : qk})
    
    # ftp connection is finite resource sec.gov only give 6? connections per ip. May be we can farm
    # this out as some point with zmq and have many workers pull data @ once and send to me
    pool = fu.FTP_Pool(5)
    q    = Queue.Queue() # Return queue

    def get_xbrl_file(cik,acc,q):
        pool.get(cik,acc,q) # Race condition failure? No anymore q now given to thread...

    th = []
    for i in TCKR_df.Acc.values:
        t = threading.Thread(target = get_xbrl_file,
                             args=(str(cik),i,q)) # Send queue as parameters to safeguard blocking
        t.start()
        th.append(t)

    for t in th: #wait for threads to finish, you have to wait
        t.join()

    # add extra column to dataframe that just has "fileloc"
    TCKR_df['Fileloc'] = ''

    # Pull out of FIFO, put back into dataframe one by one
    # will be in Quene in random order (or some function of filesize/avg internet speed)
    while not q.empty():
        ret = q.get()
        TCKR_df.loc[TCKR_df['Acc'] == ret[0],'Fileloc'] = ret[1]
    

    return TCKR_df
