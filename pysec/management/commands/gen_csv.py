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
    'ContextForDurations',
    'ContextForInstants',
    'DocumentFiscalPeriodFocus',
    'DocumentFiscalYearFocus',
    'DocumentType',
    'EntityCentralIndexKey',
    'EntityFilerCategory',
    'EntityRegistrantName',
    'FiscalYear',
    'IncomeStatementPeriodYTD',
    'TradingSymbol',
}


def create_pkl():
    forms = defaultdict(list)

    for ii in Index.objects.filter(
            form__in=['10-Q', '10-K'],
            cik__in=sym_to_ciks.values()).order_by('quarter', 'name'):
        print ii.name, ii.quarter, ii.cik
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
            forms = load_pkl()
        except IOError:
            create_pkl()
            forms = load_pkl()

        # Find all fields mentioned in any form for this symbol
        fields = set()
        for sym in forms:
            print sym
            for form in forms[sym]:
                print form['DocumentPeriodEndDate']
                fields |= set(form.keys())

            fields -= EXCLUDE_FIELDS
            filename = 'data/csv/{}.csv'.format(sym)
            with open(filename, 'w') as f:
                csv = DictWriter(f, sorted(list(fields)),
                                 extrasaction='ignore')
                csv.writeheader()
                csv.writerows(sorted(forms[sym],
                                     key=lambda x: x['DocumentPeriodEndDate']))
