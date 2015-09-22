import ftplib
from .. import edgar_config as ec
import pysec.util.edgar_utilies as eu
import os

class FTP_Connector :

    def connect(self):
        try:
            self._connection = ftplib.FTP(ec.FTP_IP)
            self._connection.login()
            return True
        except:
            return False

    def __init__(self):

        self._connection = None
        if not self.connect():
            raise Exception("Unable to connect to %s" % ec.FTP_IP)
        
    def __str__(self):
        return self._connection.getwelcome()

    def get_sec_XRBL(self,cik,acc):

        location = { 'short_cik' : eu.long_to_short_cik(cik),
                     'acc'       : eu.remove_dashes_acc(acc)}
        
        self._connection.cwd(ec.FTP_DIR % location)
        ls = self._connection.nlst()

        xml_file = None
        for i in ls:
            if ec.FTP_REGEX.search(i) is not None:
                xml_file = i; break;
        
        if xml_file is None:
            raise Exception("Can not find .xml file in FTP server on cik %s" % d['short_cik'])
        
        filename = eu.add_dashes_acc(acc) + ec.XBRL_ZIP_EXT
        
        f = open(ec.DOWNLOAD_FLDR + filename, 'wb')
        self._connection.retrbinary("RETR " + filename, f.write)
        f.close()

        os.chdir(ec.DOWNLOAD_FLDR)
        if os.system('unzip -o %s > /dev/null' % filename):
            raise Exception("Unable to unzip %s" % filename)
        
        if not os.path.isfile(xml_file):
            raise Exception("Could not find %s in %s" % (xml_file,ec.DOWNLOAD_FLDR))

        return xml_file
