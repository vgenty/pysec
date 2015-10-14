import sys
import redis
import re

BASE_URL  = u'http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=%(cik)s&type=10-%(qk)s&dateb=&owner=exclude&count=1000'
URL_ERROR = u'No matching Ticker Symbol'

ACC_NUM_REGEX = re.compile("Acc-no:\s([0-9]+-[0-9]{2}-[0-9]+)")
XBRL_REGEX    = re.compile("Interactive")

FTP_IP    = 'ftp.sec.gov'
FTP_DIR   = '/edgar/data/%(short_cik)s/%(acc)s'
FTP_REGEX = re.compile('^[a-zA-Z]+-[0-9]{8}.xml$')

XBRL_ZIP_EXT  = '-xbrl.zip'
DOWNLOAD_FLDR = '/tmp/'

SHORT_CIK_REGEX = re.compile("^[0-9]+$")
LONG_CIK_REGEX  = re.compile("^[0-9]{10}$")

# 0000005272-15-000014
DASHED_ACC_REGEX   = re.compile('^[0-9]{10}-[0-9]{2}-[0-9]{6}$')
UNDASHED_ACC_REGEX = re.compile('^[0-9]{18}$')

XBRL_DATE_KEY   = 'BalanceSheetDate'
XBRL_DATE_REGEX = re.compile('^[0-9]{4}-[0-9]{2}-[0-9]{2}$')

REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB   = 0

REDIS_CON = None
try:
    REDIS_CON = redis.StrictRedis(host = REDIS_HOST,
                                  port = REDIS_PORT,
                                  db   = REDIS_DB)
except redis.RedisError():
    print '\t Can not connect to redis database... is it on?'
    sys.exit(1)
    
RATIOS_FILE='$EDGARTOP/edgarweb/modules/pysec/resource/ratios.json'
