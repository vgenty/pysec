import pysec.edgar_config as ec

from pysec.util import ftp_connector

ftp = ftp_connector.FTP_Connector()

d = {'short_cik' : '5272' , 'acc' : '000110465909053270'}

a = ftp._connection.cwd(ec.FTP_DIR % d)
b = ftp._connection.nlst()

y = None
for i in b:
    if ec.FTP_REGEX.search(i) is not None:
        y = i; break;

print y
