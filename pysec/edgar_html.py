from __future__ import unicode_literals

from BeautifulSoup import BeautifulSoup


class EdgarHTML(object):

    def __init__(self, html):
        self.html = html
        self.soup = BeautifulSoup(html)

        self.fields = {}
        self.parse()

    def parse(self):
        # EarningsPerShare
        node = self.soup.find(text='Earnings per common share:')
        while True:
            print node
            try:
                val = float(node)
                break
            except (TypeError, ValueError):
                pass
            node = node.next
        self.fields['EarningsPerShare'] = val
