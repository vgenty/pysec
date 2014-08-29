import os
from pysec import xbrl
import lxml

from django.db import models
from django.conf import settings

DATA_DIR = settings.DATA_DIR

from sym_to_ciks import cik_to_syms

class Index(models.Model):

    filename = models.TextField()
    name = models.TextField(blank=True)
    date = models.DateField(null=True)
    cik = models.IntegerField()
    form = models.CharField(max_length=10, blank=True)
    quarter = models.CharField(max_length=6, blank=True)

    @property
    def xbrl_link(self):
        if self.form.startswith('10-K') or self.form.startswith('10-Q'):
            id = self.filename.split('/')[-1][:-4]
            return 'http://www.sec.gov/Archives/edgar/data/%s/%s/%s-xbrl.zip' % (self.cik, id.replace('-',''), id)
        return None

    @property
    def html_link(self):
        return 'http://www.sec.gov/Archives/%s' % self.filename

    @property
    def index_link(self):
        id = self.filename.split('/')[-1][:-4]
        return 'http://www.sec.gov/Archives/edgar/data/%s/%s/%s-index.htm' % (self.cik, id.replace('-',''), id)

    def txt(self):
        return self.filename.split('/')[-1]

    @property
    def localfile(self):
        filename = '%s/%s/%s/%s' % (DATA_DIR, self.cik,self.txt()[:-4],self.txt())
        if os.path.exists(filename):
            return filename
        return None

    @property
    def localpath(self):
        return '%s/%s/%s/' % (DATA_DIR, self.cik,self.txt()[:-4])

    @property
    def localcik(self):
        return '%s/%s/' % (DATA_DIR, self.cik)

    @property
    def html(self):
        filename = self.localfile
        if not filename:
            return None
        f = open(filename, 'r').read()
        f_lower = f.lower()
        try:
            return f[f_lower.find('<html>'):f_lower.find('</html>') + 4]
        except:
            print 'html tag not found'
            return f

    def download(self):
        try:
            os.mkdir(self.localcik)
        except OSError:
            pass
        try:
            os.mkdir(self.localpath)
        except OSError:
            pass

        # Complete shit
        saved_path = os.getcwd()
        os.chdir(self.localpath)

        if self.xbrl_link:
            if not os.path.exists(os.path.basename(self.xbrl_link)):
                os.system('wget -T 30 %s' % self.xbrl_link)
                os.system('unzip *.zip')
        else:
            # No xbrl, fall back to text
            if not os.path.exists(os.path.basename(self.html_link)):
                os.system('wget -T 30 %s' % self.html_link)

        os.chdir(saved_path)

    @property
    def xbrl_localpath(self):
        if not os.path.exists(self.localpath):
            self.download()
        files = os.listdir(self.localpath)
        xml = sorted([elem for elem in files if elem.endswith('.xml')],
                     key=len)
        if not len(xml):
            return None
        return self.localpath + xml[0]

    @property
    def financial_fields(self):
        x = None
        try:
            x = self.xbrl
        # TODO: this isn't my concern
        except (lxml.etree.XPathEvalError, lxml.etree.XMLSyntaxError):
            pass
        if not x:
            # TODO: fall back to parsing html
            return None
        return x.fields

    @property
    def xbrl(self):
        filepath = self.xbrl_localpath
        if not filepath:
            print 'no xbrl found. this option is for 10-ks.'
            return None
        x = xbrl.XBRL(filepath)
        x.fields['DocumentPeriodEndDate'] = x.fields['BalanceSheetDate']

        return x

    @property
    def ticker(self):
        # TODO: depends on an externally-maintained data source, but the
        # previous method of inferring the ticker from the xbrl filename would
        # occsionally return flat-out wrong results.
        return cik_to_syms.get(self.cik, None)
