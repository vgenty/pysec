#!/usr/bin/env python

from __future__ import unicode_literals

from collections import defaultdict
from django.core.management.base import NoArgsCommand
import lxml

from pysec.models import Index

from sym_to_ciks import sym_to_ciks


class Command(NoArgsCommand):

    def handle_noargs(self, **_kwargs):
        forms = defaultdict(list)

        for ii in Index.objects.filter(
                form__in=['10-Q'],
                cik__in=sym_to_ciks.values()).order_by('date', 'name'):
            print ii.name, ii.quarter
            try:
                x = ii.xbrl
            except (lxml.etree.XPathEvalError, lxml.etree.XMLSyntaxError):
                # TODO: fall back to parsing html here, I guess
                continue
            if x:
                if ii.ticker not in sym_to_ciks:
                    raise ValueError(
                        'Symbol {} is invalid - index {} {}'.format(
                            ii.ticker, ii.name, ii.quarter))
                forms[ii.ticker].append(x.fields)


        import ipdb; ipdb.set_trace()
        print x.fields
