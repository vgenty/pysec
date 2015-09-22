from lxml import etree
from xbrl_fundamentals import FundamentantalAccountingConcepts
import re


class XBRL(object):

    def __init__(self, XBRLInstanceLocation):
        self.XBRLInstanceLocation = XBRLInstanceLocation
        self.parse()

    def parse(self):
        self.fields = {}

        parser = etree.XMLParser(huge_tree=True)
        self.oInstance = etree.parse(self.XBRLInstanceLocation,
                                     parser=parser).getroot()
        self.ns = {}
        for k in self.oInstance.nsmap.keys():
            if k != None:
                self.ns[k] = self.oInstance.nsmap[k]
        self.ns['xbrli'] = 'http://www.xbrl.org/2003/instance'
        self.ns['xlmns'] = 'http://www.xbrl.org/2003/instance'

        self.context_for_instants = None
        self.contexts_for_durations = None

        self.GetBaseInformation()
        got_context = self.loadYear(0)
        if got_context:
            self.FundamentantalAccountingConcepts = (
                FundamentantalAccountingConcepts(self))

    def not_set(self, field_name):
        """
        Setting a field to zero is valid, so we check for int zero
        vs. float zero. Sounds like this sucks, so hopefully we can come up
        with something better soon.
        """
        val = self.fields[field_name]
        return val == 0 and isinstance(val, (int, long))

    def is_set(self, field_name):
        return not self.not_set(field_name)

    def loadYear(self, yearminus=0):
        got_context = False
        # Try the end period the report tells us
        # When the report is filed in february for FY ending the previous
        # december, this fails (818479/0001144204-10-009164/xray-20091231.xml)
        currentEnd = self.getNode("//dei:DocumentPeriodEndDate").text.strip()
        asdate = re.match(r'\s*(\d{4})-(\d{2})-(\d{2})\s*', currentEnd)
        if asdate:
            year = int(asdate.groups()[0]) - yearminus
            thisend = '%s-%s-%s' % (
                year, asdate.groups()[1], asdate.groups()[2])
            got_context = self.GetCurrentPeriodAndContextInformation(thisend)

        if got_context:
            return True
        # That didn't work, find the latest endDate referenced. Don't use
        # instants, because that can include the bogus, next-fiscal-year
        # date. They can include newlines, as well.
        end_dates = self.getNodeList('//xbrli:endDate')
        thisend = max(end_dates, key=lambda x: x.text).text.strip()
        got_context = self.GetCurrentPeriodAndContextInformation(thisend)
        if got_context:
            return True
        return False

    def getNodeList(self, xpath, root=None):
        if root is None:
            root = self.oInstance
        try:
            oNodelist = root.xpath(xpath, namespaces=self.ns)
        except etree.XPathEvalError:
            return []                     # TODO: ?
        return oNodelist

    def getNode(self, xpath, root=None):
        oNodelist = self.getNodeList(xpath, root)
        if len(oNodelist):
            return oNodelist[0]
        return None

    def GetFactValue(self, SeekConcept, ConceptPeriodType,
                     search_all_contexts=False):

        factValue = None

        ContextReference = {
            'Instant': self.context_for_instants,
            'Duration': self.contexts_for_durations,
            'DEI': self.context_for_dei
        }[ConceptPeriodType]

        if not ContextReference:
            return None

        if not isinstance(ContextReference, list):
            ContextReference = [ContextReference]

        # Limit to first contextreference found for old-style behavior
        use_contexts = (ContextReference if search_all_contexts
                        else ContextReference[:1])
        for context_ref in use_contexts:
            oNode = self.getNode(
                "//{SeekConcept}[@contextRef='{context_ref}']".format(
                    SeekConcept=SeekConcept, context_ref=context_ref))
            if oNode is not None:
                factValue = oNode.text
                if 'nil' in oNode.keys() and oNode.get('nil') == 'true':
                    factValue = 0
                    # set the value to ZERO if it is nil
                try:
                    factValue = float(factValue)
                except:
                    # TODO: what exception?
                    factValue = None

            if factValue:
                break
        # if factValue and context_ref != ContextReference[0]:
        #     print 'found {} at {}, not {}'.format(
        #         SeekConcept, context_ref, ContextReference[0])
        return factValue

    def GetBaseInformation(self):

        # TradingSymbol
        oNode = self.getNode("//dei:TradingSymbol[@contextRef]")
        if oNode is not None:
            self.fields['TradingSymbol'] = oNode.text
        else:
            self.fields['TradingSymbol'] = "Not provided"

        # DocumentType
        oNode = self.getNode("//dei:DocumentType[@contextRef]")
        if oNode is not None:
            self.fields['DocumentType'] = oNode.text
        else:
            self.fields['DocumentType'] = "Fiscal period focus not found"

    def GetCurrentPeriodAndContextInformation(self, EndDate):
        # Figures out the current period and contexts for the current period
        # instance/duration contexts

        self.fields['BalanceSheetDate'] = "ERROR"
        self.fields['IncomeStatementPeriodYTD'] = "ERROR"

        self.context_for_instants = "ERROR"
        self.context_for_durations = "ERROR"

        # This finds the period end date for the database table, and instant
        # date (for balance sheet):
        UseContext = "ERROR"

        def get_instant_context(nodelist_spec, find_max=False):
            """
            Concepts like Assets are as of quarter end, while concepts like
            shares outstanding seem to be at filing time. Let's get a different
            context for each. Either use EndDate, or the latest we can find if
            find_max=True.
            """
            ret_context = None
            max_date = '0000-00-00'

            oNodelist2 = self.getNodeList(nodelist_spec)
            # Nodelist of all the facts which are us-gaap:Assets
            for i in oNodelist2:

                ContextID = i.get('contextRef')

                # Nodelist of all the contexts of the facts in nodelist_spec
                oNodelist3 = self.getNodeList(
                    "//xbrli:context[@id='" + ContextID + "']")
                for j in oNodelist3:

                    # Nodes with the right period - EndDate or max
                    date = self.getNode("xbrli:period/xbrli:instant", j)
                    if date is not None:
                        if find_max:
                            # print 'Current max is {}'.format(max_date)
                            if date.text.strip() >= max_date:
                                ret_context = ContextID
                                max_date = date.text.strip()
                                # print 'New max date: {}'.format(max_date)
                                # print 'New context: {}'.format(ret_context)
                        else:
                            if date.text.strip() == EndDate:
                                oNode4 = self.getNodeList(
                                    'xbrli:entity/xbrli:segment/xbrldi:'
                                    'explicitMember', root=j)

                                if not len(oNode4):
                                    ret_context = ContextID
            return ret_context

        # Uses the concept ASSETS to find the correct instance context
        # This finds the Context ID for that end date (has correct <instant>
        # date plus has no dimensions):
        # print 'Getting context for instants'
        self.context_for_instants = get_instant_context(
            '//us-gaap:Assets | //us-gaap:AssetsCurrent |'
            '//us-gaap:LiabilitiesAndStockholdersEquity'
        )
        # print 'Getting context for DEI'
        self.context_for_dei = get_instant_context(
            '//dei:EntityCommonStockSharesOutstanding',
            find_max=True
        )

        # This finds the duration context
        # This may work incorrectly for fiscal year ends because the dates
        # cross calendar years
        # Get context ID of durations and the start date for the database table
        # print 'Getting context for duration'
        oNodelist2 = self.getNodeList(
            '//us-gaap:CashAndCashEquivalentsPeriodIncreaseDecrease | '
            '//us-gaap:CashPeriodIncreaseDecrease | '
            '//us-gaap:NetIncomeLoss | '
            '//us-gaap:NetIncomeLossAttributableToNoncontrollingInterest | '
            '//dei:DocumentPeriodEndDate')

        StartDate = "ERROR"
        StartDateYTD = "9999-01-01"
        StartDateLatest = '0000-01-01'
        UseContexts = []

        for i in oNodelist2:

            ContextID = i.get('contextRef')

            # Nodelist of all the contexts of the facts referenced above
            oNodelist3 = self.getNodeList(
                "//xbrli:context[@id='" + ContextID + "']")
            for j in oNodelist3:

                # Nodes with the right period
                if (self.getNode(
                        "xbrli:period/xbrli:endDate", j).text.strip() ==
                        EndDate):

                    oNode4 = self.getNodeList(
                        "xbrli:entity/xbrli:segment/xbrldi:explicitMember",
                        root=j)

                    if not len(oNode4):
                        # Making sure there are no dimensions. Is this the
                        # right way to do it?
                        # TODO: 926660/0000922864-12-000009/aiv-20120630.xml
                        # contains TemporaryEquityCarryingAmount only under a
                        # context with explicitMember/dimensions. I've never
                        # seen TemporaryEquity be non-zero, so I suspect this
                        # is widespread.

                        # Get the year-to-date context, not the current period
                        # MARC - this sounds wrong. I want recent, e.g., EPS,
                        # not YTD
                        StartDate = self.getNode(
                            'xbrli:period/xbrli:startDate', j).text.strip()
                        # print "Context start date: " + StartDate
                        # print "YTD start date: " + StartDateYTD

                        if StartDate < StartDateYTD:
                            # Start date is for quarter
                            # print ('Context start date is less than '
                            #        'current year to date, replace')
                            # print "Context start date (new min): " + StartDate
                            # print "Current min: " + StartDateYTD

                            StartDateYTD = StartDate
                            UseContext = j.get('id')
                            UseContexts.append((UseContext, StartDate))
                        if StartDate > StartDateLatest:
                            # Start date is for year
                            StartDateLatest = StartDate
                            UseContext = j.get('id')
                            UseContexts.append((UseContext, StartDate))
                            # print ('Context start date is greater than '
                            #        'current max, replace')
                            # print 'New latest start date:', StartDateLatest

                        # print "Use context ID: " + UseContext
                        # print "Current min: " + StartDateYTD
                        # print 'Current max:', StartDateLatest
                        # print " "

        # Balance sheet date of current period
        self.fields['BalanceSheetDate'] = EndDate

        # MsgBox "Instant context is: " + ContextForInstants
        if not self.context_for_instants:
            # MsgBox "Looking for alternative instance context"

            self.context_for_instants = (
                self.LookForAlternativeInstanceContext())

        # Income statement date for current fiscal year, year to date
        self.fields['IncomeStatementPeriodYTD'] = StartDateYTD

        self.contexts_for_durations = [c[0] for c in sorted(
            UseContexts, key=lambda x: x[1], reverse=True)]
        return self.contexts_for_durations != []

    def LookForAlternativeInstanceContext(self):
        # This deals with the situation where no instance context has no
        # dimensions. Finds something

        something = None

        # See if there are any nodes with the document period focus date
        oNodeList_Alt = self.getNodeList(
            "//xbrli:context[xbrli:period/xbrli:instant='" +
            self.fields['BalanceSheetDate'] + "']")

        # MsgBox "Node list length: " + oNodeList_Alt.length
        for oNode_Alt in oNodeList_Alt:
            # Found possible contexts
            something = self.getNode(
                "//us-gaap:Assets[@contextRef='" + oNode_Alt.get("id") + "']")
            if something is not None:
                #MsgBox "Use this context: " + oNode_Alt.selectSingleNode("@id").text
                return oNode_Alt.get("id")
