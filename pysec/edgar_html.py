from __future__ import unicode_literals

from BeautifulSoup import BeautifulSoup
import re


class EdgarHTML(object):

    def __init__(self, html):
        self.html = html
        self.soup = BeautifulSoup(html)

        self.fields = {}
        self.parse()

    def find_node(self, text):
        # Lowercase, with arbitrary whitespace
        text = '\\s*'.join(text.lower().split())
        node = self.soup.find(text=re.compile(text, re.IGNORECASE))
        return node

    def find_value(self, match):
        val = None
        node = self.find_node(match)
        while node is not None:
            try:
                val = float(node)
                break
            except (TypeError, ValueError):
                pass
            node = node.next
        return val

    def parse(self):
        # EarningsPerShare
        self.fields['EarningsPerShare'] = self.find_value(
            r'Earnings per (common)? share')

        match = re.search(r'([\d,]+)[ ]+shares of common stock',
                          self.html, re.IGNORECASE)
        if match:
            self.fields['SharesOutstanding'] = match.group(1).replace(',', '')

        match = re.search(r'CONFORMED PERIOD OF REPORT:\w+(\d)+', self.html)
        if match:
            date = match.group(1)
            date = '{}/{}/{}'.format(int(date[4:6]), date[6:8], date[2:4])
            self.fields['DocumentPeriodEndDate'] = date
        else:
            self.fields['DocumentPeriodEndDate'] = None
