import urllib2
import pandas as pd
import sys
from .. import edgar_config as ec


#
# Get pandas dataframe with columns Form type, Acc (with dashes), and time logged
#
def get_acc_table(d):

    assert 'cik' in d
    assert 'qk'  in d
    tables = None

    # this is horrible, need to use REQUEST and get error code
    # sec will always return me a page even is url is fucked
    
    request  = urllib2.Request(ec.BASE_URL % d)
    response = urllib2.urlopen(request)

    tables   = response.read()
    tables_df = pd.read_html(tables,header=0)[-1] # for some reason it's always the last idx

    assert tables_df.columns.size == 5,'Number of columns should be size 5, BAD PARSE!'
    
    # New column tells me if document will be XBRL compliant
    xbrl_yes = lambda x : ec.XBRL_REGEX.search(x) is not None
    tables_df['XBRL'] = tables_df.Format.apply(xbrl_yes)
    tables_df = tables_df[tables_df.XBRL == True]

    # print tables_df.columns
    # Remove excess
    tables_df.drop(["XBRL","Format","File/Film Number"],axis=1,inplace=True)
    
    # Regex description tag for acc
    acc_find = lambda x : ec.ACC_NUM_REGEX.search(x).group(1)
    tables_df.Description = tables_df.Description.apply(acc_find)
    tables_df.rename(columns={'Description':'Acc'}, inplace=True)
    
    # Return pandas df with columns: Fillings, Acc, Filing Data
    return tables_df

#
# CIK Utilities, 10 digit long to short, short to 10 digit long
#
def short_to_long_cik(cik):

    if not isinstance(cik,str):
        cik = str(cik)

    if is_long_cik(cik): # is already long
        return cik
    
    if len(cik) > 10: # This may be redundant
        raise Exception('Given CIK greater than 10')

    n = 10 - len(cik)

    return '0' * n + cik
    

def long_to_short_cik(cik):
    if not isinstance(cik,str):
        cik = str(cik)

    if is_short_cik(cik): # is already short
        return cik
    
    if len(cik) != 10: # This may be redundant
        raise Exception('Given CIK is not 10')

    return cik.lstrip('0')


def is_long_cik(cik):
    if ec.LONG_CIK_REGEX.search(cik) :
        return True
    
    return False

def is_short_cik(cik):
    if (ec.SHORT_CIK_REGEX.search(cik) and len(cik) < 10) :
        return True

    return False

#
# ACC Util, add or remove dashes to acc
#

def add_dashes_acc(acc):

    if not isinstance(acc,str):
        acc = str(acc)

    if is_dashed_acc(acc):
        return acc
    
    if len(acc) != 18:
        raise Exception('Given acc len not 18 as expected')

    acc = acc[:10] + '-' + acc[10:12] + '-' + acc[12:]

    return acc

def remove_dashes_acc(acc):

    if not isinstance(acc,str):
        acc = str(acc)

    if is_undashed_acc(acc):
        return acc
    
    if len(acc) != 20:
        raise Exception('Given acc len not 20 as expected')

    acc = acc.replace('-','')

    return acc

def is_dashed_acc(acc):
    if ec.DASHED_ACC_REGEX.search(acc):
        return True
    return False
    
def is_undashed_acc(acc):
    if ec.UNDASHED_ACC_REGEX.search(acc):
        return True
    return False
