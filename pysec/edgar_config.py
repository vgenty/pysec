from . import re

BASE_URL  = u'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%(cik)s&type=10-%(qk)s&dateb=&owner=exclude&count=1000'
URL_ERROR = u'No matching Ticker Symbol'

ACC_NUM_REGEX = re.compile("Acc-no:\s([0-9]+-[0-9]{2}-[0-9]+)")
XBRL_REGEX    = re.compile("Interactive")

FTP_IP    = 'ftp.sec.gov'
FTP_DIR   = '/edgar/data/%(short_cik)s/%(acc)s'
FTP_REGEX = re.compile('^[a-zA-Z]+-[0-9]{8}.xml$')
