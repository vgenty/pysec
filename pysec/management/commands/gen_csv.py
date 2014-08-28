#!/usr/bin/env python

from __future__ import unicode_literals

from django.core.management.base import NoArgsCommand
import lxml

from pysec.models import Index

from sym_to_ciks import sym_to_ciks


class Command(NoArgsCommand):

    def handle_noargs(self, **_kwargs):
        for ii in Index.objects.filter(
                form__in=['10-Q'],
                cik__in=sym_to_ciks.values()).order_by('-date'):
            print ii.name, ii.quarter
            try:
                x = ii.xbrl
            except (lxml.etree.XPathEvalError, lxml.etree.XMLSyntaxError):
                pass
            if x:
                break

        print x.fields
