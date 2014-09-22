from __future__ import unicode_literals

# TODO: do financial services companies (blackrock, AMG, etc.) have COGS at
# all? Some of the checks seem to imply not -- they would work with 0
# COGS. We're using _not_set and _is_set based on this assumption right now.

# http://xbrl.squarespace.com/journal/2013/4/4/fundamental-accounting-relations.html
# seems useful

import difflib
import pprint

from expr_parse import ExprSolver


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

    def _sum(self, *fields):
        return sum(self.xbrl.fields[f] for f in fields)

    def format_field(self, f, zero_ok=False):
        return '{}({}){}'.format(
            f, self.xbrl.fields[f], 'Z' if zero_ok else '')

    def _impute(self, left_side, right_side):
        """
        Given a set of variables that relate to each other such that

        sum(left_side) == sum(right_side),

        attempt to impute any missing values.
        """

        if not isinstance(left_side, tuple):
            left_side = (left_side,)
        if not isinstance(right_side, tuple):
            right_side = (right_side,)

        zero_ok_fields = [f[0] for f in left_side + right_side
                          if isinstance(f, tuple) and f[1] == 'zerook']
        left_side = [f[0] if isinstance(f, tuple) else f for f in left_side]
        right_side = [f[0] if isinstance(f, tuple) else f for f in right_side]

        unset_fields = [f for f in left_side + right_side
                        if self.xbrl.not_set(f) and f not in zero_ok_fields]
        if len(unset_fields) > 1:
            # Too many unknowns
            return
        if len(unset_fields) == 0:
            # All fields are set except the ones allowed to be unset -- we can
            # set it now
            if (len(zero_ok_fields) == 1 and
                    self.xbrl.not_set(zero_ok_fields[0])):
                # We can set this now
                unset_fields = [zero_ok_fields[0]]
            else:
                # Nothing to do
                return
        # We know there's only one
        field = unset_fields[0]

        left_side_sum = sum(self.xbrl.fields[f] for f in left_side
                            if self.xbrl.is_set(f))
        right_side_sum = sum(self.xbrl.fields[f] for f in right_side
                             if self.xbrl.is_set(f))
        if field in left_side:
            value = right_side_sum - left_side_sum
        else:
            value = left_side_sum - right_side_sum
        print '{}: Imputed {}: {}  from {} == {}'.format(
            self.impute_count, field, value,
            '+'.join([self.format_field(f, f in zero_ok_fields)
                      for f in left_side]),
            '+'.join([self.format_field(f, f in zero_ok_fields)
                      for f in right_side])
        )
        self.xbrl.fields[field] = value
        # TODO: get rid of this
        self.xbrl.fields['Changed'] = self.xbrl.fields.get('Changed', 0) + 1

    def first_valid_field(self, fieldnames, concept_period_type='Duration',
                          search_all_contexts=False):
        val = 0
        for fieldname in fieldnames:
            use_concept = concept_period_type
            # HACK: if fieldname is a tuple, split it to get the concept period
            # type.
            if isinstance(fieldname, tuple):
                fieldname, use_concept = fieldname
            val = self.xbrl.GetFactValue(fieldname, use_concept,
                                         search_all_contexts)
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
        self.impute_count = 0
        while old_fields != self.xbrl.fields:
            old_fields = self.xbrl.fields.copy()
            self.impute()
            self.impute_count += 1
            if self.impute_count >= 10:
                print dict_diff(old_fields, self.xbrl.fields)
                raise ValueError('Failed to converge after 10 iterations')
        return self.impute_count - 1

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

        # ExtraordinaryItemsGainLoss
        self.xbrl.fields['ExtraordinaryItemsGainLoss'] = self.xbrl.GetFactValue("us-gaap:ExtraordinaryItemNetOfTax", "Duration")
        if self.xbrl.fields['ExtraordinaryItemsGainLoss'] == None:
            self.xbrl.fields['ExtraordinaryItemsGainLoss'] = 0

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
        self.xbrl.fields['NetCashFlow'] = self.first_valid_field(
            [
                'us-gaap:CashAndCashEquivalentsPeriodIncreaseDecrease',
                'us-gaap:CashPeriodIncreaseDecrease',
                'us-gaap:NetCashProvidedByUsedInContinuingOperations',
            ],
            'Duration',
            search_all_contexts=True
        )

        # NetCashFlowsDiscontinued
        self.xbrl.fields['NetCashFlowsDiscontinued'] = self.first_valid_field(
            [
                'us-gaap:NetCashProvidedByUsedInDiscontinuedOperations',
            ],
            'Duration',
            search_all_contexts=True
        )

        # NetCashFlowsOperating/Investing/Financing{Continuing/Discontinued}
        for flow_type in ['Operating', 'Investing', 'Financing']:
            self.xbrl.fields['NetCashFlows{}'.format(flow_type)] = (
                self.first_valid_field(
                    [
                        'us-gaap:NetCashProvidedByUsedIn{}Activities'.format(
                            flow_type),
                    ],
                    'Duration',
                    search_all_contexts=True
                )
            )
            # NetCashFlowsXXX{Continuing/Discontinued}
            for st in ['Continuing', 'Discontinued']:
                self.xbrl.fields['NetCashFlows{}{}'.format(flow_type, st)] = (
                    self.first_valid_field(
                        [
                            ('us-gaap:NetCashProvidedByUsedIn{}Activities'
                             '{}Operations'.format(flow_type, st)),
                        ],
                        'Duration',
                        search_all_contexts=True
                    )
                )

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

    def impute(self):

        # BS Adjustments
        # if total assets is missing, try using current assets
        if ((self.xbrl.fields['Assets'] ==
             self.xbrl.fields['LiabilitiesAndEquity']) or
                (self.xbrl.fields['CurrentAssets'] ==
                 self.xbrl.fields['LiabilitiesAndEquity'])):
            self._impute(('Assets'), ('CurrentAssets'))

        # Added to fix Assets even more
        if (self.xbrl.not_set('NoncurrentAssets')
                and self.xbrl.is_set('LiabilitiesAndEquity')
                and (self.xbrl.fields['LiabilitiesAndEquity'] ==
                     self.xbrl.fields['Liabilities'] +
                     self.xbrl.fields['Equity'])):
            self._impute(('Assets'), ('CurrentAssets'))

        self._impute(('Assets'), ('CurrentAssets', 'NoncurrentAssets'))

        self._impute(('LiabilitiesAndEquity'), ('Assets'))

        self._impute(('Equity'),
                     ('EquityAttributableToParent',
                      ('EquityAttributableToNoncontrollingInterest',
                       'zerook')))

        # MARC - based this off of BS5 check
        self._impute(('LiabilitiesAndEquity'),
                     ('Equity', 'Liabilities',
                      ('CommitmentsAndContingencies', 'zerook'),
                      ('TemporaryEquity', 'zerook')))

        # Added to fix liabilities based on current liabilities
        self._impute(('Liabilities'),
                     ('CurrentLiabilities',
                      ('NoncurrentLiabilities', 'zerook')))

        ######### Adjustments to income statement information
        # Impute: NonoperatingIncomeLossPlusInterestAndDebtExpense
        if self.impute_count == 0:
            self.xbrl.fields[
                'NonoperatingIncomeLossPlusInterestAndDebtExpense'] = (
                    self.xbrl.fields['NonoperatingIncomeLoss'] +
                    self.xbrl.fields['InterestAndDebtExpense'])

        # Impute: Net income available to common stockholders (if it does not
        # exist)
        self._impute(('NetIncomeAttributableToParent'),
                     ('NetIncomeAvailableToCommonStockholdersBasic',
                      ('PreferredStockDividendsAndOtherAdjustments',
                       'zerook')))

        # Impute NetIncomeLoss
        self._impute(('NetIncomeLoss'),
                     ('IncomeFromContinuingOperationsAfterTax',
                      ('IncomeFromDiscontinuedOperations', 'zerook'),
                      ('ExtraordinaryItemsGainLoss', 'zerook')))

        # Impute: Net income attributable to parent if it does not exist
        self._impute(('NetIncomeLoss'),
                     ('NetIncomeAttributableToParent',
                      'NetIncomeAttributableToNoncontrollingInterest'))

        # Impute: comprehensive income
        if (self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] == 0
                and self.xbrl.fields['ComprehensiveIncomeAttributableTo'
                                     'NoncontrollingInterest'] == 0 and
                self.xbrl.fields['ComprehensiveIncome'] == 0
                and self.xbrl.fields['OtherComprehensiveIncome'] == 0):
            self.xbrl.fields['ComprehensiveIncome'] = (
                self.xbrl.fields['NetIncomeLoss'])

        # Impute: other comprehensive income
        self._impute(('ComprehensiveIncome'),
                     ('OtherComprehensiveIncome',
                      ('NetIncomeLoss', 'zerook')))

        # Impute: comprehensive income attributable to parent if it does not
        # exist
        if (self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] == 0
                and self.xbrl.fields['ComprehensiveIncomeAttributable'
                                     'ToNoncontrollingInterest'] == 0
                and self.xbrl.fields['ComprehensiveIncome'] != 0):
            self.xbrl.fields['ComprehensiveIncomeAttributableToParent'] = (
                self.xbrl.fields['ComprehensiveIncome'])

        # Impute: IncomeFromContinuingOperations*Before*Tax
        self._impute(('IncomeFromContinuingOperationsBeforeTax'),
                     ('IncomeBeforeEquityMethodInvestments',
                      'IncomeFromEquityMethodInvestments'))

        # Impute: IncomeFromContinuingOperations*Before*Tax2 (if income before
        # tax is missing)
        self._impute(('IncomeFromContinuingOperationsBeforeTax'),
                     ('IncomeFromContinuingOperationsAfterTax',
                      ('IncomeTaxExpenseBenefit')))

        # Impute: IncomeFromContinuingOperations*After*Tax
        self._impute(('IncomeFromContinuingOperationsBeforeTax'),
                     ('IncomeFromContinuingOperationsAfterTax',
                      ('IncomeTaxExpenseBenefit', 'zerook')))

        # Impute: GrossProfit
        self._impute(('Revenues'), ('GrossProfit', 'CostOfRevenue'))

        # Impute: CostsAndExpenses (would NEVER have costs and expenses if has
        # gross profit, gross profit is multi-step and costs and expenses is
        # single-step)
        self._impute(('CostsAndExpenses'),
                     ('OperatingExpenses', 'CostOfRevenue'))

        # Impute: CostsAndExpenses
        if self.xbrl.fields['GrossProfit'] == 0:
            self._impute(('Revenues'),
                         ('CostsAndExpenses', 'OperatingIncomeLoss',
                          ('OtherOperatingIncome', 'zerook')))

        # Impute: OperatingExpenses based on existence of costs and expenses
        # and cost of revenues
        self._impute(('CostsAndExpenses'),
                     ('CostOfRevenue',
                      ('OperatingExpenses', 'zerook')))

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

        # Impute: IncomeBeforeEquityMethodInvestments
        self._impute(('IncomeBeforeEquityMethodInvestments',
                      ('IncomeFromEquityMethodInvestments', 'zerook')),
                     ('IncomeFromContinuingOperationsBeforeTax'))

        # Impute: IncomeBeforeEquityMethodInvestments
        self._impute(('IncomeFromContinuingOperationsBeforeTax'),
                     ('IncomeBeforeEquityMethodInvestments',
                      'IncomeFromEquityMethodInvestments'))
        self._impute(('IncomeBeforeEquityMethodInvestments',
                      'InterestAndDebtExpense'),
                     ('OperatingIncomeLoss', 'NonoperatingIncomeLoss'))

        # Impute: OtherOperatingIncome
        self._impute(('OtherOperatingIncome', 'GrossProfit'),
                     ('OperatingIncomeLoss', 'OperatingExpenses'))

        # Move IncomeFromEquityMethodInvestments
        if (self.xbrl.fields['IncomeFromEquityMethodInvestments'] != 0
                and self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] != 0
                and self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] !=
                self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax']):
            self.xbrl.fields['IncomeBeforeEquityMethodInvestments'] = (
                self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] -
                self.xbrl.fields['IncomeFromEquityMethodInvestments'])
            # HACK: only do this decrement(?!?) on the first impute pass
            if self.impute_count == 0:
                self.xbrl.fields['OperatingIncomeLoss'] = (
                    self.xbrl.fields['OperatingIncomeLoss'] -
                    self.xbrl.fields['IncomeFromEquityMethodInvestments'])

        if self.impute_count == 0:
            self.xbrl.fields[
                'NonoperatingIncomePlusInterestAndDebtExpense'
                'PlusIncomeFromEquityMethodInvestments'] = (
                    self.xbrl.fields['IncomeFromContinuingOperationsBeforeTax'] -
                    self.xbrl.fields['OperatingIncomeLoss'])

        # NonoperatingIncomeLossPlusInterestAndDebtExpense
        self._impute(('NonoperatingIncomeLossPlusInterestAndDebtExpense',
                      'IncomeFromEquityMethodInvestments'),
                     ('NonoperatingIncomePlusInterestAndDebtExpense'
                      'PlusIncomeFromEquityMethodInvestments'))

        # Impute: total net cash flows discontinued if not reported
        self._impute(('NetCashFlowsDiscontinued'),
                     ('NetCashFlowsOperatingDiscontinued',
                      'NetCashFlowsInvestingDiscontinued',
                      'NetCashFlowsFinancingDiscontinued'))

        # Impute: cash flows from continuing
        self._impute(('NetCashFlowsOperating'),
                     ('NetCashFlowsOperatingContinuing',
                      ('NetCashFlowsOperatingDiscontinued', 'zerook')))
        self._impute(('NetCashFlowsInvesting'),
                     ('NetCashFlowsInvestingContinuing',
                      ('NetCashFlowsInvestingDiscontinued', 'zerook')))
        self._impute(('NetCashFlowsFinancing'),
                     ('NetCashFlowsFinancingContinuing',
                      ('NetCashFlowsFinancingDiscontinued', 'zerook')))

        self.xbrl.fields['NetCashFlowsContinuing'] = self._sum(
            'NetCashFlowsOperatingContinuing',
            'NetCashFlowsInvestingContinuing',
            'NetCashFlowsFinancingContinuing'
        )

        # Impute: if net cash flow is missing,: this tries to figure out the
        # value by adding up the detail. Any one detail being nonzero is enough
        # at this point
        # TODO: some kind of 'or' method for _impute would be great here
        self._impute(('NetCashFlow'),
                     ('NetCashFlowsOperating',
                      'NetCashFlowsInvesting',
                      'NetCashFlowsFinancing'))
        self._impute(('NetCashFlow'),
                     (('NetCashFlowsOperating', 'zerook'),
                      'NetCashFlowsInvesting',
                      'NetCashFlowsFinancing'))
        self._impute(('NetCashFlow'),
                     ('NetCashFlowsOperating',
                      ('NetCashFlowsInvesting', 'zerook'),
                      'NetCashFlowsFinancing'))
        self._impute(('NetCashFlow'),
                     ('NetCashFlowsOperating',
                      'NetCashFlowsInvesting',
                      ('NetCashFlowsFinancing', 'zerook')))

    def check(self):
        checks = {}

        def _check_expr(name, expr):
            solvr = ExprSolver(expr, lookup_context=self.xbrl.fields)
            solvr.verify()
            if solvr.diff:
                print '{}: {},  {}'.format(name, solvr.rendered, solvr.diff)
            checks[name] = solvr.diff

        _check_expr(
            'BS1',
            'Equity == EquityAttributableToParent + '
            'EquityAttributableToNoncontrollingInterest'
        )
        _check_expr('BS2', 'Assets == LiabilitiesAndEquity')

        if (self.xbrl.fields['CurrentAssets'] == 0
                and self.xbrl.fields['NoncurrentAssets'] == 0 and
                self.xbrl.fields['CurrentLiabilities'] == 0 and
                self.xbrl.fields['NoncurrentLiabilities'] == 0):
            # if current assets/liabilities are zero and noncurrent
            # assets/liabilities;: don't do this test because the balance sheet
            # is not classified
            _check_expr('BS3', '0 == 0')
            _check_expr('BS4', '0 == 0')

        else:
            # balance sheet IS classified
            _check_expr(
                'BS3',
                'Assets == CurrentAssets + NoncurrentAssets'
            )
            _check_expr(
                'BS4',
                'Liabilities == CurrentLiabilities + NoncurrentLiabilities'
            )

        _check_expr(
            'BS5',
            'LiabilitiesAndEquity == Liabilities'
            '+ CommitmentsAndContingencies'
            '+ TemporaryEquity'
            '+ Equity'
        )

        #### Adjustments

        _check_expr(
            'CF1',
            'NetCashFlow == '
            'NetCashFlowsOperating '
            '+ NetCashFlowsInvesting '
            '+ NetCashFlowsFinancing '
            '+ ExchangeGainsLosses'
        )
        if (checks['CF1'] != 0 and
                (self.xbrl.fields['NetCashFlow'] -
                 (self.xbrl.fields['NetCashFlowsOperating'] +
                  self.xbrl.fields['NetCashFlowsInvesting'] +
                  self.xbrl.fields['NetCashFlowsFinancing'] +
                  self.xbrl.fields['ExchangeGainsLosses']) ==
                (self.xbrl.fields['ExchangeGainsLosses'] * -1))):
            checks['CF1'] = 888888
            # What is going on here is that 171 filers compute net cash flow
            # differently than everyone else. What I am doing is marking these
            # by setting the value of the test to a number 888888 which would
            # never occur naturally, so that I can differentiate this from
            # errors.
        lngCF2 = (self.xbrl.fields['NetCashFlowsContinuing'] -
                  (self.xbrl.fields['NetCashFlowsOperatingContinuing'] +
                   self.xbrl.fields['NetCashFlowsInvestingContinuing'] +
                   self.xbrl.fields['NetCashFlowsFinancingContinuing']))
        lngCF3 = (self.xbrl.fields['NetCashFlowsDiscontinued'] -
                  (self.xbrl.fields['NetCashFlowsOperatingDiscontinued'] +
                   self.xbrl.fields['NetCashFlowsInvestingDiscontinued'] +
                   self.xbrl.fields['NetCashFlowsFinancingDiscontinued']))
        lngCF4 = (self.xbrl.fields['NetCashFlowsOperating'] -
                  (self.xbrl.fields['NetCashFlowsOperatingContinuing'] +
                   self.xbrl.fields['NetCashFlowsOperatingDiscontinued']))
        lngCF5 = (self.xbrl.fields['NetCashFlowsInvesting'] -
                  (self.xbrl.fields['NetCashFlowsInvestingContinuing'] +
                   self.xbrl.fields['NetCashFlowsInvestingDiscontinued']))
        lngCF6 = (self.xbrl.fields['NetCashFlowsFinancing'] -
                  (self.xbrl.fields['NetCashFlowsFinancingContinuing'] +
                   self.xbrl.fields['NetCashFlowsFinancingDiscontinued']))

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

        _check_expr('IS1',
                    'GrossProfit == Revenues - CostOfRevenue')
        _check_expr(
            'IS2',
            'OperatingIncomeLoss == '
            'GrossProfit - OperatingExpenses + OtherOperatingIncome')
        _check_expr('IS2_5',
                    'NonoperatingIncomeLossPlusInterestAndDebtExpense == '
                    'NonoperatingIncomeLoss + InterestAndDebtExpense')
        _check_expr('lngIS3',
                    'IncomeBeforeEquityMethodInvestments == '
                    'OperatingIncomeLoss + '
                    'NonoperatingIncomeLossPlusInterestAndDebtExpense')
        _check_expr(
            'IS4',
            'IncomeFromContinuingOperationsBeforeTax == '
            'IncomeBeforeEquityMethodInvestments '
            '+ IncomeFromEquityMethodInvestments'
        )
        _check_expr(
            'IS5',
            'IncomeFromContinuingOperationsAfterTax == '
            'IncomeFromContinuingOperationsBeforeTax - IncomeTaxExpenseBenefit'
        )
        _check_expr(
            'IS6',
            'NetIncomeLoss == IncomeFromContinuingOperationsAfterTax '
            '+ IncomeFromDiscontinuedOperations + ExtraordinaryItemsGainLoss'
        )
        _check_expr(
            'IS7',
            'NetIncomeLoss == '
            'NetIncomeAttributableToParent'
            '+ NetIncomeAttributableToNoncontrollingInterest'
        )
        _check_expr(
            'IS8',
            'NetIncomeAvailableToCommonStockholdersBasic == '
            'NetIncomeAttributableToParent'
            '- PreferredStockDividendsAndOtherAdjustments'
        )
        _check_expr(
            'IS9',
            'ComprehensiveIncome == '
            'ComprehensiveIncomeAttributableToParent '
            '+ ComprehensiveIncomeAttributableToNoncontrollingInterest'
        )
        _check_expr(
            'IS10',
            'ComprehensiveIncome == NetIncomeLoss + OtherComprehensiveIncome'
        )
        _check_expr(
            'IS11',
            'OperatingIncomeLoss == Revenues '
            '- CostsAndExpenses '
            '- OtherOperatingIncome'
        )
        # Old style
        test_names = [n for n in locals() if n not in ['self', 'failed',
                                                       '_check_expr', 'checks']]
        test_values = [locals()[n] for n in test_names]
        test_results = {k: v for k, v in zip(test_names, test_values)}
        failed_checks = [k for k, v in test_results.iteritems() if v != 0]

        # New style
        for k, v in checks.iteritems():
            if v != 0:
                failed_checks.append(k)

        self.xbrl.fields['FailedChecks'] = failed_checks

        # if self.xbrl.fields['NetCashFlow'] == 0:
        #     import ipdb; ipdb.set_trace()
        # if len(failed_checks) >= 4:
        #     print ('\n'.join(['Too many check failures:',
        #                       ', '.join(failed_checks)]))
