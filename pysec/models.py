import os
from pysec import xbrl

from django.db import models
from django.conf import settings

from edgar_html import EdgarHTML
from sym_to_ciks import cik_to_syms

DATA_DIR = settings.DATA_DIR


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
            xbrl_id = self.filename.split('/')[-1][:-4]
            return ('http://www.sec.gov/Archives/edgar/data/%s/%s/%s-xbrl.zip'
                    % (self.cik, xbrl_id.replace('-', ''), xbrl_id))
        return None

    @property
    def html_link(self):
        return 'http://www.sec.gov/Archives/%s' % self.filename

    @property
    def index_link(self):
        index_id = self.filename.split('/')[-1][:-4]
        return ('http://www.sec.gov/Archives/edgar/data/%s/%s/%s-index.htm' %
                (self.cik, index_id.replace('-', ''), index_id))

    def txt(self):
        return self.filename.split('/')[-1]

    @property
    def local_file_path(self):
        filename = '%s/%s/%s/%s' % (DATA_DIR,
                                    self.cik, self.txt()[:-4], self.txt())
        return filename

    @property
    def local_dir(self):
        return '%s/%s/%s/' % (DATA_DIR, self.cik, self.txt()[:-4])

    @property
    def localcik(self):
        return '%s/%s/' % (DATA_DIR, self.cik)

    @property
    def html(self):
        filename = self.local_file_path
        if not filename:
            return None
        if not os.path.exists(filename):
            self.download()
        f = open(filename, 'r').read()
        f_lower = f.lower()
        try:
            return f[f_lower.find('<html>'):f_lower.find('</html>') + 4]
        except:
            print 'html tag not found'
            return f

    def download(self, force_html_download=False):
        try:
            os.mkdir(self.localcik)
        except OSError:
            pass
        try:
            os.mkdir(self.local_dir)
        except OSError:
            pass

        # Complete shit
        saved_path = os.getcwd()
        os.chdir(self.local_dir)

        if self.xbrl_link:
            if not os.path.exists(os.path.basename(self.xbrl_link)):
                os.system('wget -T 30 %s' % self.xbrl_link)
                os.system('unzip *.zip')

        if force_html_download or not self.xbrl_localpath:
            # No xbrl, fall back to text
            if not os.path.exists(os.path.basename(self.html_link)):
                os.system('wget -T 30 %s' % self.html_link)

        os.chdir(saved_path)

    @property
    def xbrl_localpath(self):
        if not os.path.exists(self.local_dir):
            self.download()
        files = os.listdir(self.local_dir)
        xml = sorted([elem for elem in files if elem.endswith('.xml')
                      and elem not in ['defnref.xml']],
                     key=len)
        if not len(xml):
            return None
        return self.local_dir + xml[0]

    @property
    def financial_fields(self):
        fields = None
        if self.xbrl:
            fields = self.xbrl.fields
        if not fields:
            return None
            # TODO: html parsing not ready yet
            # fields = self.html_financial_fields
        return fields

    @property
    def xbrl(self):
        # TODO: would be nice not to calculate this every time it's accessed,
        # but we run out of memory if we do it naively
        filepath = self.xbrl_localpath
        if not filepath:
            return None
        x = xbrl.XBRL(filepath)
        x.fields['DocumentPeriodEndDate'] = x.fields['BalanceSheetDate']
        return x

    @property
    def html_financial_fields(self):
        # TODO: this name sucks, fix it.
        hh = EdgarHTML(self.html)
        return hh.fields

    @property
    def ticker(self):
        # TODO: depends on an externally-maintained data source, but the
        # previous method of inferring the ticker from the xbrl filename would
        # occsionally return flat-out wrong results.
        return cik_to_syms.get(self.cik, None)
