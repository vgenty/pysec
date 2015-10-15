from timeit import default_timer

import Queue
import threading

from .. import edgar_config as ec
import edgar_utilies as eu
import ftp_utilities as fu

import xbrl as xbrl

import sym_to_ciks as stc

import pandas as pd
import numpy as np
import json 

from datetime import datetime


def build_xbrl(df) :

    df[ 'xbrl'  ] = df['Fileloc'].apply(lambda x : xbrl.XBRL(x))
    df[ 'Date'  ] = df.apply(lambda x : eu.to_datetime(x.xbrl.fields[ec.XBRL_DATE_KEY]),axis=1)
    df['DateStr'] = df.apply(lambda x : x.Date.strftime("%B %d %Y"),axis=1)
    df.sort(['Date'],inplace=True)
        
    return df

def calculate_ratios(df) :
    df['Ratios'] = df['xbrl'].apply(ratios,axis=1)

def ratios(xbrl):
    fields = xbrl.fields
    ratios = ec.RATIOS.copy() # make a copy (ouch)

    for ana in ratios:
        for ratio in ratios[ana]:
            value = ec.ratios.parse(fields,ratios[ana][ratio])
            ratios[ana][ratio] = (ratios[ana][ratio],value)

    return ratios                   
    

    
def calculate_ratios(df):
    df['ratios'] = df['xbrl'].apply(lambda x : ratios(x.fields))
    return df # return might not be needed here

def get_company_df(ticker,qk,celery_obj=None,init_p=None):

    start_time = default_timer()
    # keep them separate for now, in the future we return them
    # in the same dataframe ordered by filing date (Q1-Q4 per year whatever)
    if qk not in ['q','k']:
        raise Exception("qk parameter is not q or k...")
    
    cik = stc.sym_to_ciks[ticker] # hopefully it's in there i don't even fucking check
    
    prefix = '10-' + qk + ': '
    
    if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': prefix+'scraping SEC web',
                                                                   'percent': init_p + 5})

    print default_timer()-start_time; start_time = default_timer()
    
    TCKR_df = eu.get_acc_table({'cik' : eu.short_to_long_cik(cik),
                                'qk'  : qk})
    print default_timer()-start_time;
    print 'Got acc table...'
    start_time = default_timer()
    if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': prefix+'opening SEC FTP FIFO',
                                                                   'percent': init_p + 10})
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
    print default_timer()-start_time;
    print 'Threaded out the fifo...'
    start_time = default_timer()
    for t in th: #wait for threads to finish, you have to wait
        t.join()

    print default_timer()-start_time;
    print 'finished waiting for sec...'
    start_time = default_timer()
    # add extra column to dataframe that just has "fileloc"
    TCKR_df['Fileloc'] = ''

    # Pull out of FIFO, put back into dataframe one by one
    # will be in Quene in random order (or some function of filesize/avg internet speed)
    
    while not q.empty():
        ret = q.get()
        TCKR_df.loc[TCKR_df['Acc'] == ret[0],'Fileloc'] = ret[1]

    print default_timer()-start_time;
    print 'pulled data out of FIFO'
    start_time = default_timer()
    if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': prefix+'downloaded XML',
                                                                   'percent': init_p + 15})
    
    if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': prefix+'building XBRL',
                                                                   'percent': init_p + 20})
    
    print default_timer()-start_time;
    print 'built XBRL objects...'
    start_time = default_timer()
    
    return TCKR_df


def get_field(row,field): # we will attempt to call this interactively...
    return row.xbrl.fields[field]
    
def get_complete_df(ticker,celery_obj=None):

    final_df = None
    
    #Should check if we already loaded this, let's check REDIS!
    if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': 'Checking redis for cache dataframe',
                                                                   'percent': 10})
    if ec.REDIS_CON.exists(ticker):
        #great its already there lets get it out, it should be missing XBRL 
        json_data = json.loads(ec.REDIS_CON.get(ticker))
        final_df  = pd.read_json(json_data)
        final_df  = build_xbrl(final_df)
        
    else: #not in database
        if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': 'searching 10-Q data form',
                                                                       'percent': 25})

        tenq_df = get_company_df(ticker,'q',celery_obj,25)

        if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': 'searching 10-K data form',
                                                                       'percent': 50})

        tenk_df = get_company_df(ticker,'k',celery_obj,50)
        if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': 'cleaning up',
                                                                   'percent': 95})

        final_df = pd.concat([tenk_df,tenq_df])

        final_df['Ticker'] = ticker
        
        if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': 'storing in redis',
                                                                       'percent': 99})



        # lets store it in redis...
        final_df.reset_index(inplace=True)

        json_df = json.dumps(final_df.to_json())
        ec.REDIS_CON.set(ticker,json_df)

        final_df  = build_xbrl(final_df)
        
        
        
    if celery_obj: celery_obj.update_state(state='PROGRESS', meta={'message': 'assembled ' + ticker + ' dataframe',
                                                                   'percent': 99})
    return final_df
