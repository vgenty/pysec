import json


ratios = {
   "Liquidity Analysis" : {
	    
     "Current Ratio" : ["CurrentAssets","/","CurrentLiabilities"],
     "Quick Ratio"   : ["Cash","+","MarketableSecurities","+","AccountsReceivable", "/","CurrentLiabilities"],
     "Cash Ratio"    : ["Cash","+","MarketableSecurities","/","AccountsReceivable"]

                          },
   "Long Term Debt and Solvency Analysis" : {

     "Debt to Capital Ratio" : ["CurrentDebt","+","LongTermDebt","/","CurrentDebt","+","LongTermDebt","+","Equity"],
     "Debt to Equity Ratio"  : ["CurrentDebt","+","LongTermDebt","/","Equity"]

                                            },
   "Return Analysis" : {

     "Return on Assets"        : ["NetIncomeLoss","/","Assets"],
     "Return on Total Capital" : ["NetIncomeLoss","/","CurrentDebt","+","LongTermDebt","+","Equity"],
     "Return on Equity"        : ["NetIncomeLoss","/","Equity"]

                       }            
}


def parse(fields,expression): #expression is a list
    denominator = 0.0
    numerator   = 0.0
    print expression
    br = expression.index("/")
    print br
    for i in expression[0:br:2] : # I see all plus signs so lets just slice on evens
        print i
        if float(fields[i]) == 0: print "bad ratio"
        print numerator
        numerator += float(fields[i])

    for i in expression[br+1:len(expression):2] : # I see all plus signs so lets just slice on evens
        if float(fields[i]) == 0: print "bad ratio"
        denominator += float(fields[i])
    

    return numerator/denominator
