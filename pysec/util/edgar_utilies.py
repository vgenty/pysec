from urllib2 import urlopen
import pandas as pd
import sys

from .. import edgar_config as ec


def get_acc_table(d):

    assert 'cik' in d
    assert 'qk'  in d
    tables = None

    # this is horrible, need to use REQUEST and get error code
    # sec will always return me a page even is url is fucked
    try:
        tables    = urlopen(ec.BASE_URL % d)
        tables    = tables.read()
    except:
        print 'Unable to open URL'
        sys.exit(1)
        
    tables_df = pd.read_html(tables,header=0)[-1] # for some reason it's always the 3rd idx
    
    # New column tells me if document will be XBRL complient
    xbrl_yes = lambda x : ec.XBRL_REGEX.search(x) is not None
    tables_df['XBRL'] = tables_df.Format.apply(xbrl_yes)
    tables_df = tables_df[tables_df.XBRL == True]

    print tables_df.columns
    # Remove excess
    tables_df.drop(["XBRL","Format","File/Film Number"],axis=1,inplace=True)
    
    # Regex description tag for acc
    acc_find = lambda x : ec.ACC_NUM_REGEX.search(x).group(1)
    tables_df.Description = tables_df.Description.apply(acc_find)
    tables_df.rename(columns={'Description':'Acc'}, inplace=True)
    
    # Return pandas df with columns: Fillings, Acc, Filing Data
    return tables_df

        
#
# CIK Utilities
#
def short_to_long_cik(cik):

    if not isinstance(cik,str):
        cik = str(cik)

    if len(cik) > 10:
        raise Exception('Given CIK greater than 10')

    n = 10 - len(cik)

    return '0' * n + cik
    
    
    
def long_to_short_cik(cik):

    if not isinstance(cik,str):
        cik = str(cik)

    if len(cik) != 10:
        raise Exception('Given CIK is not 10')

    return cik.lstrip('0')

