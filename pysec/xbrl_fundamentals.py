from __future__ import unicode_literals

# TODO: do financial services companies (blackrock, AMG, etc.) have COGS at
# all? Some of the checks seem to imply not -- they would work with 0
# COGS. We're using _not_set and _is_set based on this assumption right now.

# http://xbrl.squarespace.com/journal/2013/4/4/fundamental-accounting-relations.html
# seems useful

import difflib
import pprint


def dict_diff(d1, d2):
    diff = ('\n' + '\n'.join(difflib.ndiff(
        pprint.pformat(d1).splitlines(),
        pprint.pformat(d2).splitlines())))
    return diff


class FundamentantalAccountingConcepts(object):

    def __init__(self, xbrl):

        self.xbrl = xbrl
        self.non_imputed()
        impute_passes = self.impute_loop()
        _valid = self.check()

        print '{} impute {}'.format(impute_passes,
                                    'pass' if impute_passes == 1 else 'passes')

    def first_valid_field(self, fieldnames, concept_period_type='Duration'):
        val = 0
        for fieldname in fieldnames:
            use_concept = concept_period_type
            # HACK: if fieldname is a tuple, split it to get the concept period
            # type.
            if isinstance(fieldname, tuple):
                fieldname, use_concept = fieldname
            val = self.xbrl.GetFactValue(fieldname, use_concept)
            if val != None:
                break
        if val == None:
            val = 0
        return val

    def impute_loop(self):
        """
        Attempt to infer missing values from what we have. Returns the number
        of passes after which we converged.
        """
        old_fields = {}
        count = 0
        while old_fields != self.xbrl.fields:
            old_fields = self.xbrl.fields.copy()
            self.impute(count)
            count += 1
            if count >= 10:
                print dict_diff(old_fields, self.xbrl.fields)
                raise ValueError('Failed to converge after 10 iterations')
        return count - 1

    def print_info_block(self):
        print
        print 'FUNDAMENTAL ACCOUNTING CONCEPTS CHECK REPORT:'
        print 'XBRL instance: %s' % self.xbrl.XBRLInstanceLocation
        print ('XBRL Cloud Viewer: https://edgardashboard.xbrlcloud.com/'
               'flex/viewer/XBRLViewer.html#instance=%s') % (
                   self.xbrl.XBRLInstanceLocation)

        print 'Entity regiant name: %s' % (
            self.xbrl.fields['EntityRegistrantName'])
        print 'CIK: %s' % self.xbrl.fields['EntityCentralIndexKey']
        print 'Entity filer category: %s' % (
            self.xbrl.fields['EntityFilerCategory'])
        print 'Trading symbol: %s' % self.xbrl.fields['TradingSymbol']
        print 'Fiscal year: %s' % self.xbrl.fields['DocumentFiscalYearFocus']
        print 'Fiscal period: %s' % (
            self.xbrl.fields['DocumentFiscalPeriodFocus'])
        print 'Document type: %s' % self.xbrl.fields['DocumentType']

        print 'Balance Sheet Date (document period end date): %s' % (
            self.xbrl.fields['BalanceSheetDate'])
        print ('Income Statement Period (YTD, current period, period '
               'start date): %s to %s' % (
                   self.xbrl.fields['IncomeStatementPeriodYTD'],
                   self.xbrl.fields['BalanceSheetDate']))

        print 'Context ID for document period focus (instants): %s' % (
            self.xbrl.context_for_instants)
        print "Context ID for YTD period (durations): %s" % (
            self.xbrl.context_for_durations)
        print

    def non_imputed(self):
        # Assets
        self.xbrl.fields['Assets'] = self.xbrl.GetFactValue(
            "us-gaap:Assets", "Instant")
        if self.xbrl.fields['Assets'] == None:
            self.xbrl.fields['Assets'] = 0

        # Current Assets
        self.xbrl.fields['CurrentAssets'] = self.xbrl.GetFactValue(
            "us-gaap:AssetsCurrent", "Instant")
        if self.xbrl.fields['CurrentAssets'] == None:
            self.xbrl.fields['CurrentAssets'] = 0

        # Noncurrent Assets
        self.xbrl.fields['NoncurrentAssets'] = self.xbrl.GetFactValue(
            "us-gaap:AssetsNoncurrent", "Instant")
        if self.xbrl.fields['NoncurrentAssets'] == None:
            if (self.xbrl.fields['Assets'] and
                    self.xbrl.fields['CurrentAssets']):
                self.xbrl.fields['NoncurrentAssets'] = (
                    self.xbrl.fields['Assets'] -
                    self.xbrl.fields['CurrentAssets'])
            else:
                self.xbrl.fields['NoncurrentAssets'] = 0

        # LiabilitiesAndEquity
        self.xbrl.fields['LiabilitiesAndEquity'] = self.xbrl.GetFactValue(
            "us-gaap:LiabilitiesAndStockholdersEquity", "Instant")
        if self.xbrl.fields['LiabilitiesAndEquity'] == None:
            self.xbrl.fields['LiabilitiesAndEquity'] = self.xbrl.GetFactValue(
                "us-gaap:LiabilitiesAndPartnersCapital", "Instant")
            if self.xbrl.fields['LiabilitiesAndEquity'] == None:
                self.xbrl.fields['LiabilitiesAndEquity'] = 0

        # Liabilities
        self.xbrl.fields['Liabilities'] = self.first_valid_field(
            [
                'us-gaap:Liabilities',
                'us-gaap:AccountsPayableAndAccruedLiabilitiesCurrent',
                # TODO: this obviously includes noncurrent liabilities - get
                # those out of here --
                # 1004434/0001004434-14-000015/amg-20140630.xml
                ('us-gaap:AccountsPayableAndAccruedLiabilities'
                 'CurrentAndNoncurrent'),
            ],
            'Instant'
        )

        # CurrentLiabilities
        self.xbrl.fields['CurrentLiabilities'] = self.first_valid_field(
            ['us-gaap:LiabilitiesCurrent'], 'Instant')

        # Noncurrent Liabilities
        self.xbrl.fields['NoncurrentLiabilities'] = self.xbrl.GetFactValue("us-gaap:LiabilitiesNoncurrent", "Instant")
        if self.xbrl.fields['NoncurrentLiabilities'] == None:
            if self.xbrl.fields['Liabilities'] and self.xbrl.fields['CurrentLiabilities']:
                self.xbrl.fields['NoncurrentLiabilities'] = self.xbrl.fields['Liabilities'] - self.xbrl.fields['CurrentLiabilities']
            else:
                self.xbrl.fields['NoncurrentLiabilities'] = 0

        # CommitmentsAndContingencies
        self.xbrl.fields['CommitmentsAndContingencies'] = self.xbrl.GetFactValue("us-gaap:CommitmentsAndContingencies", "Instant")
        if self.xbrl.fields['CommitmentsAndContingencies'] == None:
            self.xbrl.fields['CommitmentsAndContingencies'] = 0

        # TemporaryEquity
        # TODO: this uses a different duration than most other fields
        self.xbrl.fields['TemporaryEquity'] = self.first_valid_field(
            [
                'us-gaap:TemporaryEquityRedemptionValue',
                'us-gaap:RedeemablePreferredStockCarryingAmount',
                'us-gaap:TemporaryEquityCarryingAmount',
                'us-gaap:TemporaryEquityValueExcludingAdditionalPaidInCapital',
                'us-gaap:TemporaryEquityCarryingAmountAttributableToParent',
                'us-gaap:RedeemableNoncontrollingInterestEquityFairValue',
                'us-gaap:TemporaryEquityStockIssuedDuringPeriodValueNewIssues',
            ],
            'Instant'
        )

        # RedeemableNoncontrollingInterest (added to temporary equity)
        RedeemableNoncontrollingInterest = None

        RedeemableNoncontrollingInterest = self.xbrl.GetFactValue(
            "us-gaap:RedeemableNoncontrollingInterestEquityCarryingAmount",
            "Instant")
        if RedeemableNoncontrollingInterest == None:
            RedeemableNoncontrollingInterest = self.xbrl.GetFactValue(
                "us-gaap:RedeemableNoncontrollingInterestEquityCommonCarryingAmount",
                "Instant")
            if RedeemableNoncontrollingInterest == None:
                RedeemableNoncontrollingInterest = 0

        # This adds redeemable noncontrolling interest and temporary equity
        # which are rare, but can be reported separately
        if self.xbrl.fields['TemporaryEquity']:
            self.xbrl.fields['TemporaryEquity'] = (
                float(self.xbrl.fields['TemporaryEquity']) +
                float(RedeemableNoncontrollingInterest))

        # Equity
        self.xbrl.fields['Equity'] = self.first_valid_field(
            [
                ('us-gaap:StockholdersEquityIncludingPortion'
                 'AttributableToNoncontrollingInterest'),
                'us-gaap:StockholdersEquity',
                ('us-gaap:PartnersCapitalIncludingPortion'
                 'AttributableToNoncontrollingInterest'),
                'us-gaap:PartnersCapital',
                'us-gaap:CommonStockholdersEquity',
                'us-gaap:MemberEquity',
                'us-gaap:AssetsNet',
                # Company-specific
                ('bcr:StockholdersEquityIncludingPortionAttributable'
                 'ToNoncontrollingInterest'),
                'ed:CommonStockEquity',
                'fmc:TotalFmcStockholdersEquity',
                'ice:TotalStockholdersEquity',
            ],
            'Instant'
        )

        # EquityAttributableToNoncontrollingInterest
        self.xbrl.fields[
            'EquityAttributableToNoncontrollingInterest'] = self.xbrl.GetFactValue("us-gaap:MinorityInterest", "Instant")
        if self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] == None:
            self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] = self.xbrl.GetFactValue("us-gaap:PartnersCapitalAttributableToNoncontrollingInterest", "Instant")
            if self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] == None:
                self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] = 0

        # EquityAttributableToParent
        self.xbrl.fields['EquityAttributableToParent'] = self.first_valid_field(
            [
                'us-gaap:StockholdersEquity',
                'us-gaap:LiabilitiesAndPartnersCapital',
            ],
            'Instant'
        )

        # Income statement

        # Revenues
        self.xbrl.fields['Revenues'] = self.first_valid_field(
            [
                'us-gaap:Revenues',
                'us-gaap:SalesRevenueNet',
                'us-gaap:SalesRevenueGoodsNet',
                'us-gaap:SalesRevenueServicesNet',
                'us-gaap:SalesRevenueServicesGross ',
                'us-gaap:SalesRevenueEnergyServices',
                'us-gaap:RevenuesNetOfInterestExpense',
                'us-gaap:RegulatedAndUnregulatedOperatingRevenue',
                'us-gaap:HealthCareOrganizationRevenue',
                'us-gaap:HealthCareOrganizationPatientServiceRevenue',
                'us-gaap:InterestAndDividendIncomeOperating',
                'us-gaap:RealEstateRevenueNet',
                'us-gaap:RevenueMineralSales',
                'us-gaap:ElectricUtilityRevenue',
                'us-gaap:OilAndGasRevenue',
                'us-gaap:RefiningAndMarketingRevenue',
                'us-gaap:FinancialServicesRevenue',
                'us-gaap:UtilityRevenue',
                'us-gaap:RegulatedAndUnregulatedOperatingRevenue',
                'us-gaap:FoodAndBeverageRevenue',
                'us-gaap:RevenueMineralSales',
                'us-gaap:AssetManagementFees',
                'us-gaap:AssetManagementFees1',   # F you, AMG
                'us-gaap:RevenuesExcludingInterestAndDividends',
                # Company-specific revenues? FML
                'fcx:RevenuesFCX',
                'fcx:RevenuesGoodsAndServices',
                # TODO: this one's not great
                ('nbr:OperatingRevenuesAndIncomeLossFrom'
                 'EquityMethodOfInvestment'),
            ],
            'Duration'
        )

        # CostOfRevenue
        self.xbrl.fields['CostOfRevenue'] = self.first_valid_field(
            [
                'us-gaap:CostOfRevenue',
                'us-gaap:CostOfServices',
                'us-gaap:CostOfGoodsSold',
                'us-gaap:CostOfGoodsAndServicesSold',
                'us-gaap:CostOfPurchasedPower',
                'us-gaap:CostOfGoldProductsAndServices',
                'us-gaap:CostOfRealEstateRevenue',
                'us-gaap:CostOfPurchasedOilAndGas',
                'us-gaap:CostOfNaturalGasPurchases',
                'us-gaap:RefiningAndMarketingCosts',
                'us-gaap:CostOfGoodsAndServicesEnergyCommoditiesAndServices',
                'us-gaap:DirectCostsOfLeasedAndRentedPropertyOrEquipment',
                # Company-specific costs of revenue
                'dd:CostOfGoodsSoldAndOtherOperatingCharges',
                'ice:RevenuesLessTransactionBasedExpenses',
                'nee:FuelPurchasedPowerAndInterchangeExpense',
                'omc:SalaryAndServiceCosts',
                'px:CostOfRevenueExcludingDepreciationandAmortization',
            ],
            'Duration'
        )

        # Rare, but until we TODO: have a sum() method, add this in
        self.xbrl.fields['CostOfRevenue'] += self.first_valid_field(
            [
                'nee:OtherOperationsAndMaintenanceExpenses',
            ],
            'Duration'
        )

        # GrossProfit
        self.xbrl.fields['GrossProfit'] = self.first_valid_field(
            [
                'us-gaap:GrossProfit',
            ],
            'Duration'
        )

        # OperatingExpenses
        self.xbrl.fields['OperatingExpenses'] = self.first_valid_field(
            [
                'us-gaap:OperatingExpenses',
                'us-gaap:OperatingCostsAndExpenses',
                'us-gaap:OtherCostAndExpenseOperating',
                'us-gaap:GeneralAndAdministrativeExpense',
                'us-gaap:SellingGeneralAndAdministrativeExpense',
                'us-gaap:OtherSellingGeneralAndAdministrativeExpense',
            ],
            'Duration'
        )

        # CostsAndExpenses
        self.xbrl.fields['CostsAndExpenses'] = self.first_valid_field(
            [
                'us-gaap:CostsAndExpenses',
            ],
            'Duration',
        )

        # OtherOperatingIncome
        self.xbrl.fields['OtherOperatingIncome'] = self.first_valid_field(
            [
                'us-gaap:OtherOperatingIncome',
            ],
            'Duration',
        )

        # OperatingIncomeLoss
        self.xbrl.fields['OperatingIncomeLoss'] = self.first_valid_field(
            [
                'us-gaap:OperatingIncomeLoss',
            ],
            'Duration',
        )

        # NonoperatingIncomeLoss
        self.xbrl.fields['NonoperatingIncomeLoss'] = self.first_valid_field(
            [
                'us-gaap:NonoperatingIncomeExpense',
                'us-gaap:RestructuringSettlementAndImpairmentProvisions',
            ],
            'Duration',
        )

        # InterestAndDebtExpense
        self.xbrl.fields['InterestAndDebtExpense'] = self.first_valid_field(
            [
                'us-gaap:InterestAndDebtExpense',
                'us-gaap:InterestExpense',
            ],
            'Duration',
        )

        # IncomeBeforeEquityMethodInvestments
        self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] = (
            self.first_valid_field(
                [
                    ('us-gaap:IncomeLossFromContinuingOperations'
                     'BeforeIncomeTaxesMinorityInterestAndIncomeLoss'
                     'FromEquityMethodInvestments'),
                ],
                'Duration',
            )
        )

        # IncomeFromEquityMethodInvestments
        self.xbrl.fields['IncomeFromEquityMethodInvestments'] = (
            self.first_valid_field(
                [
                    'us-gaap:IncomeLossFromEquityMethodInvestments',
                ],
                'Duration',
            )
        )

        # IncomeFromContinuingOperationsBeforeTax
        self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] = self.first_valid_field(
            [
                ('us-gaap:IncomeLossFromContinuingOperationsBefore'
                 'IncomeTaxesMinorityInterestAndIncomeLossFrom'
                 'EquityMethodInvestments'),
            ],
            'Duration',
        )

        # IncomeTaxExpenseBenefit
        self.xbrl.fields['IncomeTaxExpenseBenefit'] = self.xbrl.GetFactValue("us-gaap:IncomeTaxExpenseBenefit", "Duration")
        if self.xbrl.fields['IncomeTaxExpenseBenefit'] == None:
            self.xbrl.fields['IncomeTaxExpenseBenefit'] = self.xbrl.GetFactValue("us-gaap:IncomeTaxExpenseBenefitContinuingOperations", "Duration")
            if self.xbrl.fields['IncomeTaxExpenseBenefit'] == None:
                self.xbrl.fields['IncomeTaxExpenseBenefit'] = 0

        # IncomeFromContinuingOperationsAfterTax
        self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] = self.first_valid_field(
            [
                'us-gaap:IncomeLossBeforeExtraordinaryItemsAndCumulativeEffectOfChangeInAccountingPrinciple',
            ],
            'Duration',
        )

        # IncomeFromDiscontinuedOperations
        self.xbrl.fields['IncomeFromDiscontinuedOperations'] = self.xbrl.GetFactValue("us-gaap:IncomeLossFromDiscontinuedOperationsNetOfTax", "Duration")
        if self.xbrl.fields['IncomeFromDiscontinuedOperations'] == None:
            self.xbrl.fields['IncomeFromDiscontinuedOperations'] = self.xbrl.GetFactValue("us-gaap:DiscontinuedOperationGainLossOnDisposalOfDiscontinuedOperationNetOfTax", "Duration")
            if self.xbrl.fields['IncomeFromDiscontinuedOperations'] == None:
                self.xbrl.fields['IncomeFromDiscontinuedOperations'] = self.xbrl.GetFactValue("us-gaap:IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity", "Duration")
                if self.xbrl.fields['IncomeFromDiscontinuedOperations'] == None:
                    self.xbrl.fields['IncomeFromDiscontinuedOperations'] = 0

        # ExtraordaryItemsGainLoss
        self.xbrl.fields['ExtraordaryItemsGainLoss'] = self.xbrl.GetFactValue("us-gaap:ExtraordinaryItemNetOfTax", "Duration")
        if self.xbrl.fields['ExtraordaryItemsGainLoss'] == None:
            self.xbrl.fields['ExtraordaryItemsGainLoss'] = 0

        # NetIncomeLoss
        self.xbrl.fields['NetIncomeLoss'] = self.first_valid_field(
            [
                'us-gaap:ProfitLoss',
                'us-gaap:NetIncomeLoss',
                'us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic',
                'us-gaap:IncomeLossFromContinuingOperations',
                'us-gaap:IncomeLossAttributableToParent',
                ('us-gaap:IncomeLossFromContinuingOperationsIncluding'
                 'PortionAttributableToNoncontrollingInterest'),
                # Company-specific
                'cpb:IncomeLossAvailableToCommonShareholders',
            ],
            'Duration'
        )

        # Add in income reclassified from other things
        # TODO: Need a way to say NetIncomeLoss = sum(field1, field2, ...)
        # TODO: this is in some weird context we can't get yet
        self.xbrl.fields['NetIncomeLoss'] += self.first_valid_field(
            [
                ('us-gaap:DerivativeInstrumentsGainLossReclassified'
                 'FromAccumulatedOCIIntoIncomeEffectivePortionNet'),
            ],
            'Duration'
        )

        # NetIncomeAvailableToCommonStockholdersBasic
        self.xbrl.fields['NetIncomeAvailableToCommonStockholdersBasic'] = (
            self.first_valid_field(
                [
                    'us-gaap:NetIncomeLossAvailableToCommonStockholdersBasic',
                    # Company-specific
                    'cpb:IncomeLossAvailableToCommonShareholders',
                ],
                'Duration',
            )
        )

        # PreferredStockDividendsAndOtherAdjustments
        self.xbrl.fields['PreferredStockDividendsAndOtherAdjustments'] = (
            self.first_valid_field(
                [
                    'us-gaap:PreferredStockDividendsAndOtherAdjustments',
                ],
                'Duration',
            )
        )

        # NetIncomeAttributableToNoncontrollingInterest
        self.xbrl.fields['NetIncomeAttributableToNoncontrollingInterest'] = self.xbrl.GetFactValue("us-gaap:NetIncomeLossAttributableToNoncontrollingInterest", "Duration")
        if self.xbrl.fields['NetIncomeAttributableToNoncontrollingInterest'] == None:
            self.xbrl.fields['NetIncomeAttributableToNoncontrollingInterest'] = 0

        # NetIncomeAttributableToParent
        self.xbrl.fields['NetIncomeAttributableToParent'] = self.first_valid_field(
            [
                'us-gaap:NetIncomeLoss',
            ],
            'Duration',
        )

        # OtherComprehensiveIncome
        self.xbrl.fields['OtherComprehensiveIncome'] = self.xbrl.GetFactValue("us-gaap:OtherComprehensiveIncomeLossNetOfTax", "Duration")
        if self.xbrl.fields['OtherComprehensiveIncome'] == None:
            self.xbrl.fields['OtherComprehensiveIncome'] = 0

        # ComprehensiveIncome
        self.xbrl.fields['ComprehensiveIncome'] = self.xbrl.GetFactValue(
            "us-gaap:ComprehensiveIncomeNetOfTaxIncludingPortionAttributableToNoncontrollingInterest", "Duration")
        if self.xbrl.fields['ComprehensiveIncome'] == None:
            self.xbrl.fields['ComprehensiveIncome'] = self.xbrl.GetFactValue(
                "us-gaap:ComprehensiveIncomeNetOfTax", "Duration")
            if self.xbrl.fields['ComprehensiveIncome'] == None:
                self.xbrl.fields['ComprehensiveIncome'] = 0

        # ComprehensiveIncomeAttributableToParent
        self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] = self.xbrl.GetFactValue("us-gaap:ComprehensiveIncomeNetOfTax", "Duration")
        if self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] == None:
            self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] = 0

        # ComprehensiveIncomeAttributableToNoncontrollingInterest
        self.xbrl.fields['ComprehensiveIncomeAttributableToNoncontrollingInterest'] = self.xbrl.GetFactValue("us-gaap:ComprehensiveIncomeNetOfTaxAttributableToNoncontrollingInterest", "Duration")
        if self.xbrl.fields['ComprehensiveIncomeAttributableToNoncontrollingInterest'] == None:
            self.xbrl.fields['ComprehensiveIncomeAttributableToNoncontrollingInterest'] = 0

        ### MARC

        # Earnings
        self.xbrl.fields['EarningsPerShare'] = self.first_valid_field(
            [
                'us-gaap:EarningsPerShareBasic',
                'us-gaap:EarningsPerShareDiluted',
                'us-gaap:EarningsPerShareBasicAndDiluted',
            ],
            'Duration'
        )

        # Dividends
        self.xbrl.fields['DividendPerShare'] = self.first_valid_field(
            [
                'us-gaap:CommonStockDividendsPerShareDeclared',
            ],
            'Duration'
        )

        # Cash
        self.xbrl.fields['Cash'] = self.first_valid_field(
            [
                'us-gaap:Cash',
                'us-gaap:CashAndCashEquivalentsAtCarryingValue',
                'us-gaap:CashCashEquivalentsAndShortTermInvestments',
                'us-gaap:CashAndDueFromBanks',   # TODO: yes?
            ],
            'Instant'
        )

        # Securities available for sale
        self.xbrl.fields['MarketableSecurities'] = self.first_valid_field(
            [
                'us-gaap:AvailableForSaleSecurities',
                'us-gaap:AvailableForSaleSecuritiesCurrent',
                ('us-gaap:AvailableForSaleSecuritiesAndHeldTo'
                 'MaturitySecurities'),
                'us-gaap:MarketableSecuritiesCurrent',
            ],
            'Instant'
        )

        # Accounts receivable
        self.xbrl.fields['AccountsReceivable'] = self.first_valid_field(
            [
                'Us-gaap:AccountsReceivableNet',
                'us-gaap:AccountsReceivableNetCurrent',
                'us-gaap:AccountsNotesAndLoansReceivableNetCurrent',
                'us-gaap:ReceivablesNetCurrent',
                'us-gaap:PremiumsAndOtherReceivablesNet',
                'us-gaap:PremiumsReceivableAtCarryingValue',
            ],
            'Instant'
        )
        # MARC: If we don't have net accounts receivable, try for gross, and
        # subtract doubtful accounts
        if self.xbrl.not_set('AccountsReceivable'):
            self.xbrl.fields['AccountsReceivable'] = (
                self.first_valid_field(
                    [
                        'us-gaap:AccountsReceivableGrossCurrent',
                    ],
                    'Instant'
                ) -
                self.first_valid_field(
                    [
                        ('us-gaap:AllowanceForDoubtfulAccounts'
                         'ReceivableCurrent'),
                    ],
                    'Instant'
                )
            )

        # MARC: Even more accounts receivable attempts. Added together, this
        # time
        if self.xbrl.not_set('AccountsReceivable'):
            self.xbrl.fields['AccountsReceivable'] = (
                self.first_valid_field(
                    [
                        'us-gaap:ReceivablesFromCustomers',
                    ],
                    'Instant'
                ) +
                self.first_valid_field(
                    [
                        ('us-gaap:ReceivablesFromBrokersDealers'
                         'AndClearingOrganizations'),
                    ],
                    'Instant'
                )
            )

        # Shares outstanding
        self.xbrl.fields['SharesOutstanding'] = self.first_valid_field(
            [
                ('dei:EntityCommonStockSharesOutstanding', 'DEI'),
                'us-gaap:CommonStockSharesOutstanding',
            ],
            'Instant'
        )

        self.xbrl.fields['IntangibleAssets'] = self.first_valid_field(
            [
                'us-gaap:IntangibleAssetsNetExcludingGoodwill',
            ],
            'Instant'
        )

        ### Cash flow statement

        # NetCashFlow
        self.xbrl.fields['NetCashFlow'] = self.xbrl.GetFactValue(
            "us-gaap:CashAndCashEquivalentsPeriodIncreaseDecrease",
            "Duration")
        if self.xbrl.fields['NetCashFlow'] == None:
            self.xbrl.fields['NetCashFlow'] = self.xbrl.GetFactValue(
                "us-gaap:CashPeriodIncreaseDecrease",
                "Duration")
            if self.xbrl.fields['NetCashFlow'] == None:
                self.xbrl.fields['NetCashFlow'] = self.xbrl.GetFactValue(
                    "us-gaap:NetCashProvidedByUsedInContinuingOperations",
                    "Duration")
                if self.xbrl.fields['NetCashFlow'] == None:
                    self.xbrl.fields['NetCashFlow'] = 0

        # NetCashFlowsOperating
        self.xbrl.fields['NetCashFlowsOperating'] = self.xbrl.GetFactValue(
            "us-gaap:NetCashProvidedByUsedInOperatingActivities",
            "Duration")
        if self.xbrl.fields['NetCashFlowsOperating'] == None:
            self.xbrl.fields['NetCashFlowsOperating'] = 0

        # NetCashFlowsInvesting
        self.xbrl.fields['NetCashFlowsInvesting'] = self.xbrl.GetFactValue(
            "us-gaap:NetCashProvidedByUsedInInvestingActivities",
            "Duration")
        if self.xbrl.fields['NetCashFlowsInvesting'] == None:
            self.xbrl.fields['NetCashFlowsInvesting'] = 0

        # NetCashFlowsFinancing
        self.xbrl.fields['NetCashFlowsFinancing'] = self.xbrl.GetFactValue(
            "us-gaap:NetCashProvidedByUsedInFinancingActivities",
            "Duration")
        if self.xbrl.fields['NetCashFlowsFinancing'] == None:
            self.xbrl.fields['NetCashFlowsFinancing'] = 0

        # NetCashFlowsOperatingContinuing
        self.xbrl.fields[
            'NetCashFlowsOperatingContinuing'] = self.xbrl.GetFactValue(
                "us-gaap:NetCashProvidedByUsedInOperatingActivitiesContinuingOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsOperatingContinuing'] == None:
            self.xbrl.fields['NetCashFlowsOperatingContinuing'] = 0

        # NetCashFlowsInvestingContinuing
        self.xbrl.fields['NetCashFlowsInvestingContinuing'] = self.xbrl.GetFactValue("us-gaap:NetCashProvidedByUsedInInvestingActivitiesContinuingOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsInvestingContinuing'] == None:
            self.xbrl.fields['NetCashFlowsInvestingContinuing'] = 0

        # NetCashFlowsFinancingContinuing
        self.xbrl.fields['NetCashFlowsFinancingContinuing'] = self.xbrl.GetFactValue("us-gaap:NetCashProvidedByUsedInFinancingActivitiesContinuingOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsFinancingContinuing'] == None:
            self.xbrl.fields['NetCashFlowsFinancingContinuing'] = 0

        # NetCashFlowsOperatingDiscontinued
        self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] = self.xbrl.GetFactValue("us-gaap:CashProvidedByUsedInOperatingActivitiesDiscontinuedOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] ==None:
            self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] = 0

        # NetCashFlowsInvestingDiscontinued
        self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] = self.xbrl.GetFactValue("us-gaap:CashProvidedByUsedInInvestingActivitiesDiscontinuedOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] == None:
            self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] = 0

        # NetCashFlowsFinancingDiscontinued
        self.xbrl.fields['NetCashFlowsFinancingDiscontinued'] = self.xbrl.GetFactValue("us-gaap:CashProvidedByUsedInFinancingActivitiesDiscontinuedOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsFinancingDiscontinued'] == None:
            self.xbrl.fields['NetCashFlowsFinancingDiscontinued'] = 0

        # NetCashFlowsDiscontinued
        self.xbrl.fields['NetCashFlowsDiscontinued'] = self.xbrl.GetFactValue("us-gaap:NetCashProvidedByUsedInDiscontinuedOperations", "Duration")
        if self.xbrl.fields['NetCashFlowsDiscontinued'] == None:
            self.xbrl.fields['NetCashFlowsDiscontinued'] = 0

        # ExchangeGainsLosses
        self.xbrl.fields['ExchangeGainsLosses'] = self.first_valid_field(
            [
                'us-gaap:EffectOfExchangeRateOnCashAndCashEquivalents',
                ('us-gaap:EffectOfExchangeRateOnCashAndCashEquivalents'
                 'ContinuingOperations'),
                ('us-gaap:CashProvidedByUsedInFinancingActivities'
                 'DiscontinuedOperations'),
            ],
            'Duration'
        )

    def impute(self, impute_pass):

        # BS Adjustments
        # if total assets is missing, try using current assets
        if (self.xbrl.fields['Assets'] == 0
                and (self.xbrl.fields['Assets'] ==
                     self.xbrl.fields['LiabilitiesAndEquity'])
                and (self.xbrl.fields['CurrentAssets'] ==
                     self.xbrl.fields['LiabilitiesAndEquity'])):
            self.xbrl.fields['Assets'] = self.xbrl.fields['CurrentAssets']

        # MARC - same, but in reverse
        if (self.xbrl.fields['CurrentAssets'] == 0
                and (self.xbrl.fields['Assets'] ==
                     self.xbrl.fields['LiabilitiesAndEquity'])
                and (self.xbrl.fields['CurrentAssets'] ==
                     self.xbrl.fields['LiabilitiesAndEquity'])):
            self.xbrl.fields['CurrentAssets'] = self.xbrl.fields['Assets']

        # Added to fix Assets
        if (self.xbrl.fields['Assets'] == 0 and
                self.xbrl.fields['LiabilitiesAndEquity'] != 0 and
                (self.xbrl.fields['CurrentAssets'] ==
                 self.xbrl.fields['LiabilitiesAndEquity'])):
            self.xbrl.fields['Assets'] = self.xbrl.fields['CurrentAssets']

        # MARC - same, but in reverse
        if (self.xbrl.fields['CurrentAssets'] == 0 and
                self.xbrl.fields['LiabilitiesAndEquity'] != 0 and
                (self.xbrl.fields['Assets'] ==
                 self.xbrl.fields['LiabilitiesAndEquity'])):
            self.xbrl.fields['CurrentAssets'] = self.xbrl.fields['Assets']

        # Added to fix Assets even more
        if (self.xbrl.fields['Assets'] == 0
                and self.xbrl.fields['NoncurrentAssets'] == 0
                and self.xbrl.fields['LiabilitiesAndEquity'] != 0
                and (self.xbrl.fields['LiabilitiesAndEquity'] ==
                     self.xbrl.fields['Liabilities'] +
                     self.xbrl.fields['Equity'])):
            self.xbrl.fields['Assets'] = self.xbrl.fields['CurrentAssets']

        # MARC - same, but in reverse
        if (self.xbrl.fields['CurrentAssets'] == 0
                and self.xbrl.fields['NoncurrentAssets'] == 0
                and self.xbrl.fields['LiabilitiesAndEquity'] != 0
                and (self.xbrl.fields['LiabilitiesAndEquity'] ==
                     self.xbrl.fields['Liabilities'] +
                     self.xbrl.fields['Equity'])):
            self.xbrl.fields['CurrentAssets'] = self.xbrl.fields['Assets']

        if (self.xbrl.fields['NoncurrentAssets'] == 0 and
                self.xbrl.fields['Assets'] != 0 and
                self.xbrl.fields['CurrentAssets'] != 0):
            self.xbrl.fields['NoncurrentAssets'] = (
                self.xbrl.fields['Assets'] -
                self.xbrl.fields['CurrentAssets'])

        if (self.xbrl.fields['LiabilitiesAndEquity'] == 0
                and self.xbrl.fields['Assets'] != 0):
            self.xbrl.fields['LiabilitiesAndEquity'] = (
                self.xbrl.fields['Assets'])

        # Impute: Equity based on parent and noncontrolling interest being
        # present
        if (self.xbrl.fields['Equity'] == 0 and
                self.xbrl.fields[
                    'EquityAttributableToNoncontrollingInterest'] != 0 and
                self.xbrl.fields['EquityAttributableToParent'] != 0):
            self.xbrl.fields['Equity'] = (
                self.xbrl.fields['EquityAttributableToParent'] +
                self.xbrl.fields['EquityAttributableToNoncontrollingInterest'])

        if (self.xbrl.fields['Equity'] == 0 and
                self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] == 0
                and self.xbrl.fields['EquityAttributableToParent'] != 0):
            self.xbrl.fields['Equity'] = (
                self.xbrl.fields['EquityAttributableToParent'])

        # Added: Impute Equity attributable to parent based on existence of
        # equity and noncontrolling interest.
        if (self.xbrl.fields['Equity'] != 0 and
                self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] != 0
                and self.xbrl.fields['EquityAttributableToParent'] == 0):
            self.xbrl.fields['EquityAttributableToParent'] = (
                self.xbrl.fields['Equity'] -
                self.xbrl.fields['EquityAttributableToNoncontrollingInterest'])

        # Added: Impute Equity attributable to parent based on existence of
        # equity and noncontrolling interest.
        if (self.xbrl.fields['Equity'] != 0 and
            self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] == 0
            and self.xbrl.fields['EquityAttributableToParent'] == 0):
            self.xbrl.fields['EquityAttributableToParent'] = (
                self.xbrl.fields['Equity'])

        # MARC - based this off of BS5 check
        if (self.xbrl.fields['Equity'] == 0 and
                self.xbrl.is_set('LiabilitiesAndEquity') and
                self.xbrl.is_set('Liabilities')):
            self.xbrl.fields['Equity'] = (
                self.xbrl.fields['LiabilitiesAndEquity'] -
                self.xbrl.fields['Liabilities'] -
                self.xbrl.fields['CommitmentsAndContingencies'] -
                self.xbrl.fields['TemporaryEquity']
            )

        # if total liabilities is missing, figure it out based on liabilities
        # and equity
        if (self.xbrl.fields['Liabilities'] == 0 and
                self.xbrl.fields['Equity'] != 0):
            self.xbrl.fields['Liabilities'] = (
                self.xbrl.fields['LiabilitiesAndEquity'] -
                (self.xbrl.fields['CommitmentsAndContingencies'] +
                 self.xbrl.fields['TemporaryEquity'] +
                 self.xbrl.fields['Equity']))

        # This seems incorrect because liabilities might not be reported
        if (self.xbrl.fields['NoncurrentLiabilities'] == 0 and
                self.xbrl.fields['Liabilities'] != 0 and
                self.xbrl.fields['CurrentLiabilities'] != 0):
            self.xbrl.fields['NoncurrentLiabilities'] = (
                self.xbrl.fields['Liabilities'] -
                self.xbrl.fields['CurrentLiabilities'])

        # Added to fix liabilities based on current liabilities
        if self.xbrl.fields['Liabilities'] == 0 and self.xbrl.fields['CurrentLiabilities'] != 0 and self.xbrl.fields['NoncurrentLiabilities'] == 0:
            self.xbrl.fields['Liabilities'] = self.xbrl.fields['CurrentLiabilities']

        # MARC - same, but in reverse
        if (self.xbrl.fields['CurrentLiabilities'] == 0 and
                self.xbrl.fields['Liabilities'] != 0 and
                self.xbrl.fields['NoncurrentLiabilities'] == 0):
            self.xbrl.fields['CurrentLiabilities'] = self.xbrl.fields['Liabilities']

        #########'Adjustments to income statement information
        # Impute: NonoperatingIncomeLossPlusInterestAndDebtExpense
        self.xbrl.fields[
            'NonoperatingIncomeLossPlusInterestAndDebtExpense'] = (
                self.xbrl.fields['NonoperatingIncomeLoss'] +
                self.xbrl.fields['InterestAndDebtExpense'])

        # Impute: Net income available to common stockholders (if it does not
        # exist)
        if self.xbrl.fields['NetIncomeAvailableToCommonStockholdersBasic'] == 0 and self.xbrl.fields['PreferredStockDividendsAndOtherAdjustments'] == 0 and self.xbrl.fields['NetIncomeAttributableToParent'] != 0:
            self.xbrl.fields['NetIncomeAvailableToCommonStockholdersBasic'] = self.xbrl.fields['NetIncomeAttributableToParent']

        # Impute NetIncomeLoss
        if (self.xbrl.fields['NetIncomeLoss'] != 0
                and self.xbrl.fields[
                    'IncomeFromContinuingOperationsAfterTax'] == 0):
            self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] = (
                self.xbrl.fields['NetIncomeLoss'] -
                self.xbrl.fields['IncomeFromDiscontinuedOperations'] -
                self.xbrl.fields['ExtraordaryItemsGainLoss'])

        # Impute: Net income attributable to parent if it does not exist
        if (self.xbrl.fields['NetIncomeAttributableToParent'] == 0
                and self.xbrl.fields[
                    'NetIncomeAttributableToNoncontrollingInterest'] == 0
                and self.xbrl.fields['NetIncomeLoss'] != 0):
            self.xbrl.fields['NetIncomeAttributableToParent'] = (
                self.xbrl.fields['NetIncomeLoss'])

        # Impute: PreferredStockDividendsAndOtherAdjustments
        if (self.xbrl.fields['PreferredStockDividendsAndOtherAdjustments'] == 0
                and self.xbrl.fields['NetIncomeAttributableToParent'] != 0
                and self.xbrl.fields['NetIncomeAvailableTo'
                                     'CommonStockholdersBasic'] != 0):
            self.xbrl.fields['PreferredStockDividendsAndOtherAdjustments'] = (
                self.xbrl.fields['NetIncomeAttributableToParent'] -
                self.xbrl.fields['NetIncomeAvailableToCommonStockholdersBasic'])

        # Impute: comprehensive income
        if self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] == 0 and self.xbrl.fields['ComprehensiveIncomeAttributableToNoncontrollingInterest'] == 0 and self.xbrl.fields['ComprehensiveIncome'] == 0 and self.xbrl.fields['OtherComprehensiveIncome'] == 0:
            self.xbrl.fields['ComprehensiveIncome'] = self.xbrl.fields['NetIncomeLoss']

        # Impute: other comprehensive income
        if (self.xbrl.fields['ComprehensiveIncome'] != 0 and
                self.xbrl.fields['OtherComprehensiveIncome'] == 0):
            self.xbrl.fields['OtherComprehensiveIncome'] = (
                self.xbrl.fields['ComprehensiveIncome'] -
                self.xbrl.fields['NetIncomeLoss'])

        # Impute: comprehensive income attributable to parent if it does not
        # exist
        if (self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] == 0
                and self.xbrl.fields['ComprehensiveIncomeAttributable'
                                     'ToNoncontrollingInterest'] == 0
                and self.xbrl.fields['ComprehensiveIncome'] != 0):
            self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] = (
                self.xbrl.fields['ComprehensiveIncome'])

        # Impute: IncomeFromContinuingOperations*Before*Tax
        if self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] != 0 and self.xbrl.fields['IncomeFromEquityMethodInvestments'] != 0 and self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] == 0:
            self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] = self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] + self.xbrl.fields['IncomeFromEquityMethodInvestments']

        # Impute: IncomeFromContinuingOperations*Before*Tax2 (if income before
        # tax is missing)
        if self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] == 0 and self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] != 0:
            self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] = self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] + self.xbrl.fields['IncomeTaxExpenseBenefit']

        # Impute: IncomeFromContinuingOperations*After*Tax
        if self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] == 0 and \
            (self.xbrl.fields['IncomeTaxExpenseBenefit'] !=0 or self.xbrl.fields['IncomeTaxExpenseBenefit'] == 0) and self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] != 0:
            self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] = self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] - self.xbrl.fields['IncomeTaxExpenseBenefit']

        # Impute: GrossProfit
        if (self.xbrl.fields['GrossProfit'] == 0 and
                self.xbrl.fields['Revenues'] != 0 and
                self.xbrl.is_set('CostOfRevenue')):
            self.xbrl.fields['GrossProfit'] = (
                self.xbrl.fields['Revenues'] -
                self.xbrl.fields['CostOfRevenue'])

        # Impute: Revenues
        if (self.xbrl.fields['GrossProfit'] != 0 and
                self.xbrl.fields['Revenues'] == 0 and
                self.xbrl.is_set('CostOfRevenue')):
            self.xbrl.fields['Revenues'] = (self.xbrl.fields['GrossProfit'] +
                                            self.xbrl.fields['CostOfRevenue'])
        # Impute: CostOfRevenue
        if (self.xbrl.fields['GrossProfit'] != 0 and
                self.xbrl.fields['Revenues'] != 0 and
                self.xbrl.not_set('CostOfRevenue')):
            self.xbrl.fields['CostOfRevenue'] = (
                self.xbrl.fields['GrossProfit'] + self.xbrl.fields['Revenues'])

        # Impute: CostsAndExpenses (would NEVER have costs and expenses if has
        # gross profit, gross profit is multi-step and costs and expenses is
        # single-step)
        if (self.xbrl.fields['GrossProfit'] == 0
                and self.xbrl.fields['CostsAndExpenses'] == 0
                and self.xbrl.is_set('CostOfRevenue')
                and self.xbrl.fields['OperatingExpenses'] != 0):
            self.xbrl.fields['CostsAndExpenses'] = (
                self.xbrl.fields['CostOfRevenue'] +
                self.xbrl.fields['OperatingExpenses'])

        # Impute: CostsAndExpenses based on existence of both costs of revenues
        # and operating expenses
        if (self.xbrl.fields['CostsAndExpenses'] == 0
                and self.xbrl.fields['OperatingExpenses'] != 0
                and self.xbrl.is_set('CostOfRevenue')):
            self.xbrl.fields['CostsAndExpenses'] = (
                self.xbrl.fields['CostOfRevenue'] +
                self.xbrl.fields['OperatingExpenses'])

        # Impute: CostsAndExpenses
        if (self.xbrl.fields['GrossProfit'] == 0
                and self.xbrl.fields['CostsAndExpenses'] == 0
                and self.xbrl.fields['Revenues'] != 0
                and self.xbrl.fields['OperatingIncomeLoss'] != 0
                # MARC - this is sometimes entirely zero, let's see if it's bad
                # to ignore it
                # and self.xbrl.fields['OtherOperatingIncome'] != 0
        ):
            self.xbrl.fields['CostsAndExpenses'] = (
                self.xbrl.fields['Revenues'] -
                self.xbrl.fields['OperatingIncomeLoss'] -
                self.xbrl.fields['OtherOperatingIncome'])

        # Impute: OperatingExpenses based on existence of costs and expenses
        # and cost of revenues
        if (self.xbrl.is_set('CostOfRevenue') and
                self.xbrl.fields['CostsAndExpenses'] != 0 and
                self.xbrl.fields['OperatingExpenses'] == 0):
            self.xbrl.fields['OperatingExpenses'] = (
                self.xbrl.fields['CostsAndExpenses'] -
                self.xbrl.fields['CostOfRevenue'])
            self.xbrl.fields['Changed'] = 'HAAAAAACK'

        # Impute: CostOfRevenues single-step method
        if (self.xbrl.fields['Revenues'] != 0 and
                self.xbrl.fields['GrossProfit'] == 0 and
                (self.xbrl.fields['Revenues'] -
                 self.xbrl.fields['CostsAndExpenses'] ==
                 self.xbrl.fields['OperatingIncomeLoss']) and
                self.xbrl.fields['OperatingExpenses'] == 0 and
                self.xbrl.fields['OtherOperatingIncome'] == 0):
            self.xbrl.fields['CostOfRevenue'] = (
                self.xbrl.fields['CostsAndExpenses'] -
                self.xbrl.fields['OperatingExpenses'])

        # MARC: last-ditch CostOfRevenue
        if (self.xbrl.not_set('CostOfRevenue') and
                self.xbrl.fields['CostsAndExpenses'] != 0):
            self.xbrl.fields['CostOfRevenue'] = (
                self.xbrl.fields['CostsAndExpenses'] -
                self.xbrl.fields['OperatingExpenses'])

        # Impute: IncomeBeforeEquityMethodInvestments
        if (self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] == 0 and
                self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] != 0):
            self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] = (
                self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] -
                self.xbrl.fields['IncomeFromEquityMethodInvestments'])

        # Impute: IncomeBeforeEquityMethodInvestments
        if (self.xbrl.fields['OperatingIncomeLoss'] != 0
                and self.xbrl.fields['NonoperatingIncomeLoss'] != 0
                and self.xbrl.fields['InterestAndDebtExpense'] == 0
                and self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] != 0):
            self.xbrl.fields['InterestAndDebtExpense'] = (
                self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] -
                (self.xbrl.fields['OperatingIncomeLoss'] +
                 self.xbrl.fields['NonoperatingIncomeLoss']))

        # Impute: OtherOperatingIncome
        if (self.xbrl.fields['GrossProfit'] != 0 and
                self.xbrl.fields['OperatingExpenses'] != 0
                and self.xbrl.fields['OperatingIncomeLoss'] != 0):
            self.xbrl.fields['OtherOperatingIncome'] = (
                self.xbrl.fields['OperatingIncomeLoss'] -
                (self.xbrl.fields['GrossProfit'] -
                 self.xbrl.fields['OperatingExpenses']))

        # Move IncomeFromEquityMethodInvestments
        if (self.xbrl.fields['IncomeFromEquityMethodInvestments'] != 0
                and self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] != 0
                and self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] !=
                self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax']):
            self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] = (
                self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] -
                self.xbrl.fields['IncomeFromEquityMethodInvestments'])
            # HACK: only do this decrement(?!?) on the first impute pass
            if impute_pass == 0:
                self.xbrl.fields['OperatingIncomeLoss'] = (
                    self.xbrl.fields['OperatingIncomeLoss'] -
                    self.xbrl.fields['IncomeFromEquityMethodInvestments'])

        # DANGEROUS!!  May need to turn off. IS3 had 2085 PASSES WITHOUT this
        # imputing. if it is higher,: keep the test
        # Impute: OperatingIncomeLoss
        if (self.xbrl.fields['OperatingIncomeLoss'] == 0
                and self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] != 0):
            self.xbrl.fields['OperatingIncomeLoss'] = (
                self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] +
                self.xbrl.fields['NonoperatingIncomeLoss'] -
                self.xbrl.fields['InterestAndDebtExpense'])


        self.xbrl.fields['NonoperatingIncomePlusInterestAndDebtExpensePlusIncomeFromEquityMethodInvestments'] = self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] - self.xbrl.fields['OperatingIncomeLoss']

        # NonoperatingIncomeLossPlusInterestAndDebtExpense
        if self.xbrl.fields['NonoperatingIncomeLossPlusInterestAndDebtExpense'] == 0 and self.xbrl.fields['NonoperatingIncomePlusInterestAndDebtExpensePlusIncomeFromEquityMethodInvestments'] != 0:
            self.xbrl.fields['NonoperatingIncomeLossPlusInterestAndDebtExpense'] = self.xbrl.fields['NonoperatingIncomePlusInterestAndDebtExpensePlusIncomeFromEquityMethodInvestments'] - self.xbrl.fields['IncomeFromEquityMethodInvestments']

        # Impute: total net cash flows discontinued if not reported
        if self.xbrl.fields['NetCashFlowsDiscontinued'] == 0:
            self.xbrl.fields['NetCashFlowsDiscontinued'] = (
                self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] +
                self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] +
                self.xbrl.fields['NetCashFlowsFinancingDiscontinued'])

        # Impute: cash flows from continuing
        if (self.xbrl.fields['NetCashFlowsOperating'] != 0 and
                self.xbrl.fields['NetCashFlowsOperatingContinuing'] == 0):
            self.xbrl.fields['NetCashFlowsOperatingContinuing'] = (
                self.xbrl.fields['NetCashFlowsOperating'] -
                self.xbrl.fields['NetCashFlowsOperatingDiscontinued'])
        if (self.xbrl.fields['NetCashFlowsInvesting'] != 0 and
                self.xbrl.fields['NetCashFlowsInvestingContinuing'] == 0):
            self.xbrl.fields['NetCashFlowsInvestingContinuing'] = (
                self.xbrl.fields['NetCashFlowsInvesting'] -
                self.xbrl.fields['NetCashFlowsInvestingDiscontinued'])
        if (self.xbrl.fields['NetCashFlowsFinancing'] != 0 and
                self.xbrl.fields['NetCashFlowsFinancingContinuing'] == 0):
            self.xbrl.fields['NetCashFlowsFinancingContinuing'] = (
                self.xbrl.fields['NetCashFlowsFinancing'] -
                self.xbrl.fields['NetCashFlowsFinancingDiscontinued'])


        if self.xbrl.fields['NetCashFlowsOperating'] == 0 and self.xbrl.fields['NetCashFlowsOperatingContinuing'] != 0 and self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] == 0:
            self.xbrl.fields['NetCashFlowsOperating'] = self.xbrl.fields['NetCashFlowsOperatingContinuing']
        if self.xbrl.fields['NetCashFlowsInvesting'] == 0 and self.xbrl.fields['NetCashFlowsInvestingContinuing'] != 0 and self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] == 0:
            self.xbrl.fields['NetCashFlowsInvesting'] = self.xbrl.fields['NetCashFlowsInvestingContinuing']
        if self.xbrl.fields['NetCashFlowsFinancing'] == 0 and self.xbrl.fields['NetCashFlowsFinancingContinuing'] != 0 and self.xbrl.fields['NetCashFlowsFinancingDiscontinued'] == 0:
            self.xbrl.fields['NetCashFlowsFinancing'] = self.xbrl.fields['NetCashFlowsFinancingContinuing']

        self.xbrl.fields['NetCashFlowsContinuing'] = self.xbrl.fields['NetCashFlowsOperatingContinuing'] + self.xbrl.fields['NetCashFlowsInvestingContinuing'] + self.xbrl.fields['NetCashFlowsFinancingContinuing']

        # Impute: if net cash flow is missing,: this tries to figure out the
        # value by adding up the detail
        if (self.xbrl.fields['NetCashFlow'] == 0 and
                (self.xbrl.fields['NetCashFlowsOperating'] != 0 or
                 self.xbrl.fields['NetCashFlowsInvesting'] != 0 or
                 self.xbrl.fields['NetCashFlowsFinancing'] != 0)):
            self.xbrl.fields['NetCashFlow'] = (
                self.xbrl.fields['NetCashFlowsOperating'] +
                self.xbrl.fields['NetCashFlowsInvesting'] +
                self.xbrl.fields['NetCashFlowsFinancing'])

    def check(self):
        lngBSCheck1 = (self.xbrl.fields['Equity'] -
                       (self.xbrl.fields['EquityAttributableToParent'] +
                        self.xbrl.fields['EquityAttributableTo'
                                         'NoncontrollingInterest']))
        lngBSCheck2 = (self.xbrl.fields['Assets'] -
                       self.xbrl.fields['LiabilitiesAndEquity'])

        if (self.xbrl.fields['CurrentAssets'] == 0
                and self.xbrl.fields['NoncurrentAssets'] == 0 and
                self.xbrl.fields['CurrentLiabilities'] == 0 and
                self.xbrl.fields['NoncurrentLiabilities'] == 0):
            # if current assets/liabilities are zero and noncurrent
            # assets/liabilities;: don't do this test because the balance sheet
            # is not classified
            lngBSCheck3 = 0
            lngBSCheck4 = 0

        else:
            # balance sheet IS classified
            lngBSCheck3 = (self.xbrl.fields['Assets'] -
                           (self.xbrl.fields['CurrentAssets'] +
                            self.xbrl.fields['NoncurrentAssets']))
            lngBSCheck4 = (self.xbrl.fields['Liabilities'] -
                           (self.xbrl.fields['CurrentLiabilities'] +
                            self.xbrl.fields['NoncurrentLiabilities']))

        lngBSCheck5 = (self.xbrl.fields['LiabilitiesAndEquity'] -
                       (self.xbrl.fields['Liabilities'] +
                        self.xbrl.fields['CommitmentsAndContingencies'] +
                        self.xbrl.fields['TemporaryEquity'] +
                        self.xbrl.fields['Equity']))

        if lngBSCheck1:
            print "BS1: Equity(" , self.xbrl.fields['Equity'] , ") = EquityAttributableToParent(" , self.xbrl.fields['EquityAttributableToParent'] , ") , EquityAttributableToNoncontrollingInterest(" , self.xbrl.fields['EquityAttributableToNoncontrollingInterest'] , "): " , lngBSCheck1
        if lngBSCheck2:
            print "BS2: Assets(" , self.xbrl.fields['Assets'] , ") = LiabilitiesAndEquity(" , self.xbrl.fields['LiabilitiesAndEquity'] , "): " , lngBSCheck2
        if lngBSCheck3:
            print "BS3: Assets(" , self.xbrl.fields['Assets'] , ") = CurrentAssets(" , self.xbrl.fields['CurrentAssets'] , ") , NoncurrentAssets(" , self.xbrl.fields['NoncurrentAssets'] , "): " , lngBSCheck3
        if lngBSCheck4:
            print "BS4: Liabilities(" , self.xbrl.fields['Liabilities'] , ") = CurrentLiabilities(" , self.xbrl.fields['CurrentLiabilities'] , ") , NoncurrentLiabilities(" , self.xbrl.fields['NoncurrentLiabilities'] , "): " , lngBSCheck4
        if lngBSCheck5:
            print "BS5: Liabilities and Equity(" , self.xbrl.fields['LiabilitiesAndEquity'] , ") = Liabilities(" , self.xbrl.fields['Liabilities'] , ") , CommitmentsAndContingencies(" , self.xbrl.fields['CommitmentsAndContingencies'] , "), TemporaryEquity(" , self.xbrl.fields['TemporaryEquity'] , "), Equity(" , self.xbrl.fields['Equity'] , "): " , lngBSCheck5

        #### Adjustments

        lngCF1 = self.xbrl.fields['NetCashFlow'] - (self.xbrl.fields['NetCashFlowsOperating'] + self.xbrl.fields['NetCashFlowsInvesting'] + self.xbrl.fields['NetCashFlowsFinancing'] + self.xbrl.fields['ExchangeGainsLosses'])
        if lngCF1!=0 and (self.xbrl.fields['NetCashFlow'] - (self.xbrl.fields['NetCashFlowsOperating'] + self.xbrl.fields['NetCashFlowsInvesting'] + self.xbrl.fields['NetCashFlowsFinancing'] + self.xbrl.fields['ExchangeGainsLosses']) == (self.xbrl.fields['ExchangeGainsLosses'] * -1)):
            lngCF1 = 888888
            # What is going on here is that 171 filers compute net cash flow
            # differently than everyone else. What I am doing is marking these
            # by setting the value of the test to a number 888888 which would
            # never occur naturally, so that I can differentiate this from
            # errors.
        lngCF2 = self.xbrl.fields['NetCashFlowsContinuing'] - (self.xbrl.fields['NetCashFlowsOperatingContinuing'] + self.xbrl.fields['NetCashFlowsInvestingContinuing'] + self.xbrl.fields['NetCashFlowsFinancingContinuing'])
        lngCF3 = self.xbrl.fields['NetCashFlowsDiscontinued'] - (self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] + self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] + self.xbrl.fields['NetCashFlowsFinancingDiscontinued'])
        lngCF4 = self.xbrl.fields['NetCashFlowsOperating'] - (self.xbrl.fields['NetCashFlowsOperatingContinuing'] + self.xbrl.fields['NetCashFlowsOperatingDiscontinued'])
        lngCF5 = self.xbrl.fields['NetCashFlowsInvesting'] - (self.xbrl.fields['NetCashFlowsInvestingContinuing'] + self.xbrl.fields['NetCashFlowsInvestingDiscontinued'])
        lngCF6 = self.xbrl.fields['NetCashFlowsFinancing'] - (self.xbrl.fields['NetCashFlowsFinancingContinuing'] + self.xbrl.fields['NetCashFlowsFinancingDiscontinued'])

        if lngCF1:
            print "CF1: NetCashFlow(" , self.xbrl.fields['NetCashFlow'] , ") = (NetCashFlowsOperating(" , self.xbrl.fields['NetCashFlowsOperating'] , ") , (NetCashFlowsInvesting(" , self.xbrl.fields['NetCashFlowsInvesting'] , ") , (NetCashFlowsFinancing(" , self.xbrl.fields['NetCashFlowsFinancing'] , ") , ExchangeGainsLosses(" , self.xbrl.fields['ExchangeGainsLosses'] , "): " , lngCF1
        if lngCF2:
            print "CF2: NetCashFlowsContinuing(" , self.xbrl.fields['NetCashFlowsContinuing'] , ") = NetCashFlowsOperatingContinuing(" , self.xbrl.fields['NetCashFlowsOperatingContinuing'] , ") , NetCashFlowsInvestingContinuing(" , self.xbrl.fields['NetCashFlowsInvestingContinuing'] , ") , NetCashFlowsFinancingContinuing(" , self.xbrl.fields['NetCashFlowsFinancingContinuing'] , "): " , lngCF2
        if lngCF3:
            print "CF3: NetCashFlowsDiscontinued(" , self.xbrl.fields['NetCashFlowsDiscontinued'] , ") = NetCashFlowsOperatingDiscontinued(" , self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] , ") , NetCashFlowsInvestingDiscontinued(" , self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] , ") , NetCashFlowsFinancingDiscontinued(" , self.xbrl.fields['NetCashFlowsFinancingDiscontinued'] , "): " , lngCF3
        if lngCF4:
            print "CF4: NetCashFlowsOperating(" , self.xbrl.fields['NetCashFlowsOperating'] , ") = NetCashFlowsOperatingContinuing(" , self.xbrl.fields['NetCashFlowsOperatingContinuing'] , ") , NetCashFlowsOperatingDiscontinued(" , self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] , "): " , lngCF4
        if lngCF5:
            print "CF5: NetCashFlowsInvesting(" , self.xbrl.fields['NetCashFlowsInvesting'] , ") = NetCashFlowsInvestingContinuing(" , self.xbrl.fields['NetCashFlowsInvestingContinuing'] , ") , NetCashFlowsInvestingDiscontinued(" , self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] , "): " , lngCF5
        if lngCF6:
            print "CF6: NetCashFlowsFinancing(" , self.xbrl.fields['NetCashFlowsFinancing'] , ") = NetCashFlowsFinancingContinuing(" , self.xbrl.fields['NetCashFlowsFinancingContinuing'] , ") , NetCashFlowsFinancingDiscontinued(" , self.xbrl.fields['NetCashFlowsFinancingDiscontinued'] , "): " , lngCF6

        lngIS1 = ((self.xbrl.fields['Revenues'] -
                   self.xbrl.fields['CostOfRevenue']) -
                  self.xbrl.fields['GrossProfit'])
        lngIS2 = ((self.xbrl.fields['GrossProfit'] -
                   self.xbrl.fields['OperatingExpenses'] +
                   self.xbrl.fields['OtherOperatingIncome']) -
                  self.xbrl.fields['OperatingIncomeLoss'])
        lngIS3 = (self.xbrl.fields['OperatingIncomeLoss'] + self.xbrl.fields['NonoperatingIncomeLossPlusInterestAndDebtExpense']) - self.xbrl.fields['IncomeBeforeEquityMethodInvestments']
        lngIS4 = (self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] + self.xbrl.fields['IncomeFromEquityMethodInvestments']) - self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax']
        lngIS5 = (self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] - self.xbrl.fields['IncomeTaxExpenseBenefit']) - self.xbrl.fields['IncomeFromContinuingOperationsAfterTax']
        lngIS6 = (self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] + self.xbrl.fields['IncomeFromDiscontinuedOperations'] + self.xbrl.fields['ExtraordaryItemsGainLoss']) - self.xbrl.fields['NetIncomeLoss']
        lngIS7 = (self.xbrl.fields['NetIncomeAttributableToParent'] + self.xbrl.fields['NetIncomeAttributableToNoncontrollingInterest']) - self.xbrl.fields['NetIncomeLoss']
        lngIS8 = (self.xbrl.fields['NetIncomeAttributableToParent'] - self.xbrl.fields['PreferredStockDividendsAndOtherAdjustments']) - self.xbrl.fields['NetIncomeAvailableToCommonStockholdersBasic']
        lngIS9 = ((self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] +
                   self.xbrl.fields['ComprehensiveIncomeAttributable'
                                    'ToNoncontrollingInterest']) -
                  self.xbrl.fields['ComprehensiveIncome'])
        lngIS10 = ((self.xbrl.fields['NetIncomeLoss'] +
                    self.xbrl.fields['OtherComprehensiveIncome']) -
                   self.xbrl.fields['ComprehensiveIncome'])
        lngIS11 = self.xbrl.fields['OperatingIncomeLoss'] - (self.xbrl.fields['Revenues'] - self.xbrl.fields['CostsAndExpenses'] + self.xbrl.fields['OtherOperatingIncome'])

        if lngIS1:
            print "IS1: GrossProfit(" , self.xbrl.fields['GrossProfit'] , ") = Revenues(" , self.xbrl.fields['Revenues'] , ") - CostOfRevenue(" , self.xbrl.fields['CostOfRevenue'] , "): " , lngIS1
        if lngIS2:
            print "IS2: OperatingIncomeLoss(" , self.xbrl.fields['OperatingIncomeLoss'] , ") = GrossProfit(" , self.xbrl.fields['GrossProfit'] , ") - OperatingExpenses(" , self.xbrl.fields['OperatingExpenses'] , ") , OtherOperatingIncome(" , self.xbrl.fields['OtherOperatingIncome'] , "): " , lngIS2
        if lngIS3:
            print "IS3: IncomeBeforeEquityMethodInvestments(" , self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] , ") = OperatingIncomeLoss(" , self.xbrl.fields['OperatingIncomeLoss'] , ") - NonoperatingIncomeLoss(" , self.xbrl.fields['NonoperatingIncomeLoss'] , "), InterestAndDebtExpense(" , self.xbrl.fields['InterestAndDebtExpense'] , "): " , lngIS3
        if lngIS4:
            print "IS4: IncomeFromContinuingOperationsBeforeTax(" , self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] , ") = IncomeBeforeEquityMethodInvestments(" , self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] , ") , IncomeFromEquityMethodInvestments(" , self.xbrl.fields['IncomeFromEquityMethodInvestments'] , "): " , lngIS4

        if lngIS5:
            print "IS5: IncomeFromContinuingOperationsAfterTax(" , self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] , ") = IncomeFromContinuingOperationsBeforeTax(" , self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] , ") - IncomeTaxExpenseBenefit(" , self.xbrl.fields['IncomeTaxExpenseBenefit'] , "): " , lngIS5
        if lngIS6:
            print "IS6: NetIncomeLoss(" , self.xbrl.fields['NetIncomeLoss'] , ") = IncomeFromContinuingOperationsAfterTax(" , self.xbrl.fields['IncomeFromContinuingOperationsAfterTax'] , ") , IncomeFromDiscontinuedOperations(" , self.xbrl.fields['IncomeFromDiscontinuedOperations'] , ") , ExtraordaryItemsGainLoss(" , self.xbrl.fields['ExtraordaryItemsGainLoss'] , "): " , lngIS6
        if lngIS7:
            print "IS7: NetIncomeLoss(" , self.xbrl.fields['NetIncomeLoss'] , ") = NetIncomeAttributableToParent(" , self.xbrl.fields['NetIncomeAttributableToParent'] , ") , NetIncomeAttributableToNoncontrollingInterest(" , self.xbrl.fields['NetIncomeAttributableToNoncontrollingInterest'] , "): " , lngIS7
        if lngIS8:
            print "IS8: NetIncomeAvailableToCommonStockholdersBasic(" , self.xbrl.fields['NetIncomeAvailableToCommonStockholdersBasic'] , ") = NetIncomeAttributableToParent(" , self.xbrl.fields['NetIncomeAttributableToParent'] , ") - PreferredStockDividendsAndOtherAdjustments(" , self.xbrl.fields['PreferredStockDividendsAndOtherAdjustments'] , "): " , lngIS8
        if lngIS9:
            print "IS9: ComprehensiveIncome(" , self.xbrl.fields['ComprehensiveIncome'] , ") = ComprehensiveIncomeAttributableToParent(" , self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] , ") , ComprehensiveIncomeAttributableToNoncontrollingInterest(" , self.xbrl.fields['ComprehensiveIncomeAttributableToNoncontrollingInterest'] , "): " , lngIS9
        if lngIS10:
            print "IS10: ComprehensiveIncome(" , self.xbrl.fields['ComprehensiveIncome'] , ") = NetIncomeLoss(" , self.xbrl.fields['NetIncomeLoss'] , ") , OtherComprehensiveIncome(" , self.xbrl.fields['OtherComprehensiveIncome'] , "): " , lngIS10
        if lngIS11:
            print "IS11: OperatingIncomeLoss(" , self.xbrl.fields['OperatingIncomeLoss'] , ") = Revenues(" , self.xbrl.fields['Revenues'] , ") - CostsAndExpenses(" , self.xbrl.fields['CostsAndExpenses'] , ") , OtherOperatingIncome(" , self.xbrl.fields['OtherOperatingIncome'] , "): " , lngIS11

        test_names = [n for n in locals() if n not in ['self', 'failed']]
        test_values = [locals()[n] for n in test_names]
        test_results = {k: v for k, v in zip(test_names, test_values)}

        # if self.xbrl.fields['IntangibleAssets'] == 0:
        #     import ipdb; ipdb.set_trace()
        # failed_tests = [k for k, v in test_results.iteritems() if v != 0]
        # if len(failed_tests) >= 4:
        #     print ('\n'.join(['Too many check failures:',
        #                       ', '.join(failed_tests)]))
