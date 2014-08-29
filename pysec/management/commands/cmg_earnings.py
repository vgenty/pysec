from __future__ import unicode_literals

from pysec.models import Index


from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):

    def handle_noargs(self, **_kwargs):
        ii = list(Index.objects.filter(
            form='10-Q', cik='1058090').order_by('date'))[0]
        x = ii.financial_fields
        import ipdb; ipdb.set_trace()
        print 'Earnings:', x.fields['EarningsPerShare']
        print 'Revenue:', x.fields['Revenues']
