import ftplib
from .. import edgar_config as ec

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
