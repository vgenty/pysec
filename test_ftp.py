import pysec.edgar_config as ec
import os

from pysec.util import ftp_connector

ftp = ftp_connector.FTP_Connector()

d = {'short_cik' : '5272' , 'acc' : '000110465909053270'}

a = ftp._connection.cwd(ec.FTP_DIR % d)
b = ftp._connection.nlst()

y = None
for i in b:
    if ec.FTP_REGEX.search(i) is not None:
        y = i; break;

if y is None:
    raise Exception("Can not find .xml file in FTP server on cik %s" % d['short_cik'])

acc = '0001104659-09-053270'
filename = acc + ec.XBRL_ZIP_EXT

f = open(ec.DOWNLOAD_FLDR + filename, 'wb')
ftp._connection.retrbinary("RETR " + filename, f.write)
f.close()

os.chdir(ec.DOWNLOAD_FLDR)
if os.system('unzip -o %s > /dev/null' % filename):
    raise Exception("Unable to unzip %s" % filename)

if not os.path.isfile(y):
    raise Exception("Could not find %s in %s" % (y,ec.DOWNLOAD_FLDR))
