#!/usr/bin/env python

from __future__ import unicode_literals

from collections import defaultdict
from csv import DictWriter
from django.core.management.base import NoArgsCommand
import pickle

from pysec.models import Index

from sym_to_ciks import sym_to_ciks

PICKLE_FILE = 'forms.pkl'

# Fields we don't need in our CSVs
EXCLUDE_FIELDS = {
    'BalanceSheetDate',
    'Changed',
    'ContextForDurations',
    'ContextForInstants',
    'DocumentFiscalPeriodFocus',
    'DocumentFiscalYearFocus',
    'DocumentType',
    'EmptyFieldNames',
    'EntityCentralIndexKey',
    'EntityFilerCategory',
    'EntityRegistrantName',
    'FailedChecks',
    'FiscalYear',
    'IncomeStatementPeriodYTD',
    'TradingSymbol',
}


def create_pkl():
    forms = defaultdict(list)

    for ii in (Index
               .objects
               .filter(form__in=['10-Q', '10-K'],
                       cik__in=sym_to_ciks.values())
                       # cik__in=[1390777])
               .order_by('quarter', 'name')
               # .order_by('?')
    ):
        print ii.name, ii.quarter, ii.cik, ii.local_dir
        ff = ii.financial_fields
        if not ff:
            continue
        if ii.ticker not in sym_to_ciks:
            raise ValueError(
                'Symbol {} is invalid - index {} {}'.format(
                    ii.ticker, ii.name, ii.quarter))
        forms[ii.ticker].append(ff)
    with open(PICKLE_FILE, 'w') as f:
        pickle.dump(forms, f)


def load_pkl():
    with open(PICKLE_FILE) as f:
        return pickle.load(f)


class Command(NoArgsCommand):

    def handle_noargs(self, **_kwargs):
        try:
            sym_to_forms = load_pkl()
        except IOError:
            create_pkl()
            sym_to_forms = load_pkl()

        # Find all fields mentioned in any form for this symbol
        fields = set()
        empty_fields = defaultdict(int)
        failed_checks = defaultdict(int)

        for sym in sym_to_forms:
            print sym
            for form in sym_to_forms[sym]:
                for fieldname in form['EmptyFieldNames']:
                    empty_fields[fieldname] += 1
                # TODO: if this value isn't present, XBRLFundamentals failed.
                for checkname in form.get('FailedChecks', []):
                    failed_checks[checkname] += 1
                fields |= set(form.keys())

            fields -= EXCLUDE_FIELDS
            filename = 'data/csv/{}.csv'.format(sym)
            with open(filename, 'w') as f:
                csv = DictWriter(f, sorted(list(fields)),
                                 extrasaction='ignore')
                csv.writeheader()
                csv.writerows(sorted(sym_to_forms[sym],
                                     key=lambda x: x['DocumentPeriodEndDate']))

        num_forms = sum(len(v) for v in sym_to_forms.values())
        for k, v in sorted(empty_fields.items(), key=lambda x: x[1],
                           reverse=True):
            print '{}: {}'.format(k, v)
        print
        print 'Total empty fields: {}, {:.02f} per form'.format(
            sum(empty_fields.values()),
            sum(empty_fields.values()) / float(num_forms))
        print
        for k, v in sorted(failed_checks.items(), key=lambda x: x[1],
                           reverse=True):
            print '{}: {}'.format(k, v)
        print 'Total failed checks: {}, {:.02f} per form'.format(
            sum(failed_checks.values()),
            sum(failed_checks.values()) / float(num_forms))
        print
        print 'Total forms: {}'.format(num_forms)
