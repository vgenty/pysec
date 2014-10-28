import os
import urllib

from django.core.management.base import NoArgsCommand
from django.conf import settings

from pysec.models import Index
from zipfile import ZipFile

from sym_to_ciks import sym_to_ciks

CIKS = sym_to_ciks.values()

DATA_DIR = settings.DATA_DIR

ALWAYS_DOWNLOAD = True

def removeNonAscii(s):
    return "".join(i for i in s if ord(i) < 128)


# Gets the list of filings and download locations for the given year and
# quarter
def get_filing_list(year, qtr):
    url = 'ftp://ftp.sec.gov/edgar/full-index/%d/QTR%d/company.zip' % (year, qtr)
    quarter = "%s%s" % (year, qtr)

    print url

    # Download the data and save to a file
    fn = '%s/company_%d_%d.zip' % (DATA_DIR, year, qtr)

    if (not os.path.exists(fn)) or (ALWAYS_DOWNLOAD):
        print 'Downloading data'
        compressed_data = urllib.urlopen(url).read()
        fileout = open(fn, 'w')
        fileout.write(compressed_data)
        fileout.close()

    # Extract the compressed file
    zip_file = ZipFile(fn)
    zdata = zip_file.read('company.idx')
    zdata = removeNonAscii(zdata)

    # Parse the fixed-length fields
    result = []
    for r in zdata.split('\n')[10:]:
        date = r[86:98].strip()
        if date == '':
            date = None
        if r.strip() == '':
            continue
        filing = {'name': r[0:62].strip(),
                  'form': r[62:74].strip(),
                  'cik': r[74:86].strip(),
                  'date': date,
                  'quarter': quarter,
                  'filename': r[98:].strip()}
        try:
            if int(filing['cik']) not in CIKS:
                continue
        except ValueError:
            print 'Problem with filing: {}'.format(filing)
            continue

        result.append(Index(**filing))

    return result


class Command(NoArgsCommand):
    help = "Download new files representing one month of 990s, ignoring months we already have. Each quarter contains hundreds of thousands of filings; will take a while to run. "


    def handle_noargs(self, **_options):

        print "LIMITING TO CIKS IN sym_to_ciks"

        for year in range(2009, 2015):
            for qtr in range(1, 5):
                quarter = "%s%s" % (year, qtr)
                Index.objects.filter(quarter=quarter).delete()
                objs = get_filing_list(year, qtr)
                for i, obj in enumerate(objs):
                    if i % 100 == 0:
                        print i, obj.name, obj.quarter
                    try:
                        obj.save()
                    except:
                        print 'error: %s' % obj
                print i, obj.name, obj.quarter
