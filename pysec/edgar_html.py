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
            r'Earnings per (common)? share:')
