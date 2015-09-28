import Queue
import threading

from .. import edgar_config as ec

import edgar_utilies as eu
import ftp_utilities as fu
import xbrl as xbrl

import sym_to_ciks as stc

import pandas as pd

from datetime import datetime

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
    

    y = lambda x : xbrl.XBRL(x)
    TCKR_df['xbrl'] = TCKR_df['Fileloc'].apply(y)
    
    return TCKR_df

def get_date(row):
    date = row.xbrl.fields[ec.XBRL_DATE_KEY]
    return eu.to_datetime(date)

def get_field(row,field): # we will attempt to call this interactively...
    return row.xbrl.fields[field]
    
def get_complete_df(ticker):
    tenq_df = get_company_df(ticker,'q')
    tenk_df = get_company_df(ticker,'k')

    final_df = pd.concat([tenk_df,tenq_df])
    print final_df.columns
    final_df['Date'] = final_df.apply(get_date,axis=1)
    
    final_df.sort(['Date'],inplace=True)
    
    return final_df
