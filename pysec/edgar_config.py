BASE_URL  = u'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%(cik)s&type=10-%(qk)s&dateb=&owner=exclude&count=1000'
URL_ERROR = u'No matching Ticker Symbol'

from . import re
ACC_NUM_REGEX = re.compile("Acc-no:\s([0-9]+-[0-9][0-9]-[0-9]+)")
XBRL_REGEX    = re.compile("Interactive")

FTP_IP = 'ftp.sec.gov'
