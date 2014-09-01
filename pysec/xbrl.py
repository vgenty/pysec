from lxml import etree
from xbrl_fundamentals import FundamentantalAccountingConcepts
import re


class XBRL(object):

    def __init__(self, XBRLInstanceLocation):

        self.XBRLInstanceLocation = XBRLInstanceLocation
        self.fields = {}

        parser = etree.XMLParser(huge_tree=True)
        self.oInstance = etree.parse(XBRLInstanceLocation,
                                     parser=parser).getroot()
        self.ns = {}
        for k in self.oInstance.nsmap.keys():
            if k != None:
                self.ns[k] = self.oInstance.nsmap[k]
        self.ns['xbrli'] = 'http://www.xbrl.org/2003/instance'
        self.ns['xlmns'] = 'http://www.xbrl.org/2003/instance'

        self.context_for_instants = None
        self.context_for_durations = None

        self.GetBaseInformation()
        got_context = self.loadYear(0)
        if got_context:
            self.FundamentantalAccountingConcepts = (
                FundamentantalAccountingConcepts(self))

    def loadYear(self, yearminus=0):
        got_context = False
        # Try the end period the report tells us
        # When the report is filed in february for FY ending the previous
        # december, this fails (818479/0001144204-10-009164/xray-20091231.xml)
        currentEnd = self.getNode("//dei:DocumentPeriodEndDate").text
        asdate = re.match(r'\s*(\d{4})-(\d{2})-(\d{2})\s*', currentEnd)
        if asdate:
            year = int(asdate.groups()[0]) - yearminus
            thisend = '%s-%s-%s' % (
                year, asdate.groups()[1], asdate.groups()[2])
            got_context = self.GetCurrentPeriodAndContextInformation(thisend)

        if got_context:
            return True
        # That didn't work, find the latest endDate referenced. Don't use
        # instants, because that can include the bogus, next-fiscal-year date.
        end_dates = self.getNodeList('//xbrli:endDate')
        thisend = max(end_dates, key=lambda x: x.text).text
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

    def GetFactValue(self, SeekConcept, ConceptPeriodType):

        factValue = None

        if ConceptPeriodType == "Instant":
            ContextReference = self.context_for_instants
        elif ConceptPeriodType == "Duration":
            ContextReference = self.context_for_durations
        else:
            # An error occured
            return "CONTEXT ERROR"

        if not ContextReference:
            return None

        oNode = self.getNode(
            "//" + SeekConcept + "[@contextRef='" + ContextReference + "']")
        if oNode is not None:
            factValue = oNode.text
            if 'nil' in oNode.keys() and oNode.get('nil') == 'true':
                factValue = 0
                # set the value to ZERO if it is nil
            # if type(factValue)==str:
            try:
                factValue = float(factValue)
            except:
                # print 'couldnt convert %s=%s to float' %
                # (SeekConcept, factValue)
                factValue = None

        return factValue

    def GetBaseInformation(self):

        # Registered Name
        oNode = self.getNode("//dei:EntityRegistrantName[@contextRef]")
        if oNode is not None:
            self.fields['EntityRegistrantName'] = oNode.text
        else:
            self.fields['EntityRegistrantName'] = "Registered name not found"

        # Fiscal year
        oNode = self.getNode("//dei:CurrentFiscalYearEndDate[@contextRef]")
        if oNode is not None:
            self.fields['FiscalYear'] = oNode.text
        else:
            self.fields['FiscalYear'] = "Fiscal year not found"

        # EntityCentralIndexKey
        oNode = self.getNode("//dei:EntityCentralIndexKey[@contextRef]")
        if oNode is not None:
            self.fields['EntityCentralIndexKey'] = oNode.text
        else:
            self.fields['EntityCentralIndexKey'] = "CIK not found"

        # EntityFilerCategory
        oNode = self.getNode("//dei:EntityFilerCategory[@contextRef]")
        if oNode is not None:
            self.fields['EntityFilerCategory'] = oNode.text
        else:
            self.fields['EntityFilerCategory'] = "Filer category not found"

        # TradingSymbol
        oNode = self.getNode("//dei:TradingSymbol[@contextRef]")
        if oNode is not None:
            self.fields['TradingSymbol'] = oNode.text
        else:
            self.fields['TradingSymbol'] = "Not provided"

        # DocumentFiscalYearFocus
        oNode = self.getNode("//dei:DocumentFiscalYearFocus[@contextRef]")
        if oNode is not None:
            self.fields['DocumentFiscalYearFocus'] = oNode.text
        else:
            self.fields['DocumentFiscalYearFocus'] = (
                "Fiscal year focus not found")

        # DocumentFiscalPeriodFocus
        oNode = self.getNode("//dei:DocumentFiscalPeriodFocus[@contextRef]")
        if oNode is not None:
            self.fields['DocumentFiscalPeriodFocus'] = oNode.text
        else:
            self.fields['DocumentFiscalPeriodFocus'] = (
                "Fiscal period focus not found")

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
        # EndDate = self.getNode("//dei:DocumentPeriodEndDate").text
        # This is the <instant> or the <endDate>

        # Uses the concept ASSETS to find the correct instance context
        # This finds the Context ID for that end date (has correct <instant>
        # date plus has no dimensions):
        oNodelist2 = self.getNodeList(
            '//us-gaap:Assets | //us-gaap:AssetsCurrent |'
            '//us-gaap:LiabilitiesAndStockholdersEquity')
        # Nodelist of all the facts which are us-gaap:Assets
        for i in oNodelist2:
            # print i.XML

            ContextID = i.get('contextRef')
            ContextPeriod = self.getNode("//xbrli:context[@id='" + ContextID +
                 "']/xbrli:period/xbrli:instant").text
            print 'ContextPeriod:', ContextPeriod

            # Nodelist of all the contexts of the fact us-gaap:Assets
            oNodelist3 = self.getNodeList(
                "//xbrli:context[@id='" + ContextID + "']")
            for j in oNodelist3:

                # Nodes with the right period
                if (self.getNode("xbrli:period/xbrli:instant", j) is not None
                        and self.getNode(
                            "xbrli:period/xbrli:instant", j).text == EndDate):

                    oNode4 = self.getNodeList(
                        "xbrli:entity/xbrli:segment/xbrldi:explicitMember", j)

                    if not len(oNode4):
                        UseContext = ContextID
                        # print UseContext

        ContextForInstants = UseContext
        self.context_for_instants = ContextForInstants

        # This finds the duration context
        # This may work incorrectly for fiscal year ends because the dates
        # cross calendar years
        # Get context ID of durations and the start date for the database table
        oNodelist2 = self.getNodeList(
            '//us-gaap:CashAndCashEquivalentsPeriodIncreaseDecrease | '
            '//us-gaap:CashPeriodIncreaseDecrease | '
            '//us-gaap:NetIncomeLoss | '
            '//dei:DocumentPeriodEndDate')

        StartDate = "ERROR"
        StartDateYTD = "2099-01-01"
        StartDateLatest = '0000-01-01'
        UseContext = "ERROR"

        for i in oNodelist2:
            # print i.XML

            ContextID = i.get('contextRef')

            # ContextPeriod = self.getNode(
            #     "//xbrli:context[@id='" + ContextID + "']/xbrli:period/xbrli:endDate")
            # print ContextPeriod

            # Nodelist of all the contexts of the facts referenced above
            oNodelist3 = self.getNodeList(
                "//xbrli:context[@id='" + ContextID + "']")
            for j in oNodelist3:

                # Nodes with the right period
                if self.getNode(
                        "xbrli:period/xbrli:endDate", j).text == EndDate:

                    oNode4 = self.getNodeList(
                        "xbrli:entity/xbrli:segment/xbrldi:explicitMember", j)

                    if not len(oNode4):
                        # Making sure there are no dimensions. Is this the
                        # right way to do it?

                        # Get the year-to-date context, not the current period
                        # MARC - this sounds wrong. I want recent, e.g., EPS,
                        # not YTD
                        StartDate = self.getNode(
                            'xbrli:period/xbrli:startDate', j).text
                        print "Context start date: " + StartDate
                        print "YTD start date: " + StartDateYTD

                        if StartDate < StartDateYTD:
                            # Start date is for quarter
                            print ('Context start date is less than '
                                   'current year to date, replace')
                            print "Context start date (new min): " + StartDate
                            print "Current min: " + StartDateYTD

                            StartDateYTD = StartDate
                        if StartDate > StartDateLatest:
                            # Start date is for year
                            StartDateLatest = StartDate
                            UseContext = j.get('id')
                            print ('Context start date is greater than '
                                   'current max, replace')
                            print 'New latest start date:', StartDateLatest

                        print "Use context ID: " + UseContext
                        print "Current min: " + StartDateYTD
                        print 'Current max:', StartDateLatest
                        print " "

        # Balance sheet date of current period
        self.fields['BalanceSheetDate'] = EndDate

        # MsgBox "Instant context is: " + ContextForInstants
        if ContextForInstants == "ERROR":
            # MsgBox "Looking for alternative instance context"

            ContextForInstants = self.LookForAlternativeInstanceContext()
            self.context_for_instants = ContextForInstants

        # Income statement date for current fiscal year, year to date
        self.fields['IncomeStatementPeriodYTD'] = StartDateYTD

        ContextForDurations = UseContext
        self.context_for_durations = ContextForDurations
        return ContextForDurations != 'ERROR'

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
            # MsgBox oNode_Alt.selectSingleNode("@id").text
            something = self.getNode(
                "//us-gaap:Assets[@contextRef='" + oNode_Alt.get("id") + "']")
            if something:
                #MsgBox "Use this context: " + oNode_Alt.selectSingleNode("@id").text
                return oNode_Alt.get("id")
