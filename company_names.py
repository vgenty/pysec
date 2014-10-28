from __future__ import unicode_literals

from BeautifulSoup import BeautifulSoup
import re
import requests

from sym_to_ciks import sym_to_ciks

symbols_sp500 = ('A', 'AA', 'AAPL', 'ABBV', 'ABC', 'ABT', 'ACE', 'ACN', 'ACT',
                 'ADBE', 'ADI', 'ADM', 'ADP', 'ADS', 'ADSK', 'ADT', 'AEE',
                 'AEP', 'AES', 'AET', 'AFL', 'AGN', 'AIG', 'AIV', 'AIZ',
                 'AKAM', 'ALL', 'ALLE', 'ALTR', 'ALXN', 'AMAT', 'AME', 'AMG',
                 'AMGN', 'AMP', 'AMT', 'AMZN', 'AN', 'AON', 'APA', 'APC',
                 'APD', 'APH', 'ARG', 'ATI', 'AVB', 'AVGO', 'AVP', 'AVY',
                 'AXP', 'AZO', 'BA', 'BAC', 'BAX', 'BBBY', 'BBT', 'BBY', 'BCR',
                 'BDX', 'BEN', 'BHI', 'BIIB', 'BK', 'BLK', 'BLL', 'BMS', 'BMY',
                 'BRCM', 'BSX', 'BTU', 'BWA', 'BXP', 'C', 'CA', 'CAG', 'CAH',
                 'CAM', 'CAT', 'CB', 'CBG', 'CBS', 'CCE', 'CCI', 'CCL', 'CELG',
                 'CERN', 'CF', 'CFN', 'CHK', 'CHRW', 'CI', 'CINF', 'CL', 'CLX',
                 'CMA', 'CMCSA', 'CME', 'CMG', 'CMI', 'CMS', 'CNP', 'CNX',
                 'COF', 'COG', 'COH', 'COL', 'COP', 'COST', 'COV', 'CPB',
                 'CRM', 'CSC', 'CSCO', 'CSX', 'CTAS', 'CTL', 'CTSH', 'CTXS',
                 'CVC', 'CVS', 'CVX', 'D', 'DAL', 'DD', 'DE', 'DFS', 'DG',
                 'DGX', 'DHI', 'DHR', 'DIS', 'DISCA', 'DLPH', 'DLTR', 'DNB',
                 'DNR', 'DO', 'DOV', 'DOW', 'DPS', 'DRI', 'DTE', 'DTV', 'DUK',
                 'DVA', 'DVN', 'EA', 'EBAY', 'ECL', 'ED', 'EFX', 'EIX', 'EL',
                 'EMC', 'EMN', 'EMR', 'EOG', 'EQR', 'EQT', 'ESRX', 'ESS',
                 'ESV', 'ETFC', 'ETN', 'ETR', 'EW', 'EXC', 'EXPD', 'EXPE', 'F',
                 'FAST', 'FB', 'FCX', 'FDO', 'FDX', 'FE', 'FFIV', 'FIS',
                 'FISV', 'FITB', 'FLIR', 'FLR', 'FLS', 'FMC', 'FOSL', 'FOXA',
                 'FSLR', 'FTI', 'FTR', 'GAS', 'GCI', 'GD', 'GE', 'GGP', 'GHC',
                 'GILD', 'GIS', 'GLW', 'GM', 'GMCR', 'GME', 'GNW', 'GOOGL',
                 'GPC', 'GPS', 'GRMN', 'GS', 'GT', 'GWW', 'HAL', 'HAR', 'HAS',
                 'HBAN', 'HCBK', 'HCN', 'HCP', 'HD', 'HES', 'HIG', 'HOG',
                 'HON', 'HOT', 'HP', 'HPQ', 'HRB', 'HRL', 'HRS', 'HSP', 'HST',
                 'HSY', 'HUM', 'IBM', 'ICE', 'IFF', 'INTC', 'INTU', 'IP',
                 'IPG', 'IR', 'IRM', 'ISRG', 'ITW', 'IVZ', 'JBL', 'JCI', 'JEC',
                 'JNJ', 'JNPR', 'JOY', 'JPM', 'JWN', 'K', 'KEY', 'KIM', 'KLAC',
                 'KMB', 'KMI', 'KMX', 'KO', 'KORS', 'KR', 'KRFT', 'KSS', 'KSU',
                 'L', 'LB', 'LEG', 'LEN', 'LH', 'LLL', 'LLTC', 'LLY', 'LM',
                 'LMT', 'LNC', 'LO', 'LRCX', 'LUK', 'LUV', 'LYB', 'M', 'MA',
                 'MAC', 'MAR', 'MAS', 'MAT', 'MCD', 'MCHP', 'MCK', 'MCO',
                 'MDLZ', 'MDT', 'MET', 'MHFI', 'MHK', 'MJN', 'MKC', 'MLM',
                 'MMC', 'MMM', 'MNST', 'MO', 'MON', 'MOS', 'MPC', 'MRK', 'MRO',
                 'MS', 'MSFT', 'MSI', 'MTB', 'MU', 'MUR', 'MWV', 'MYL', 'NAVI',
                 'NBL', 'NBR', 'NDAQ', 'NE', 'NEE', 'NEM', 'NFLX', 'NFX', 'NI',
                 'NKE', 'NLSN', 'NOC', 'NOV', 'NRG', 'NSC', 'NTAP', 'NTRS',
                 'NU', 'NUE', 'NVDA', 'NWL', 'NWSA', 'OI', 'OKE', 'OMC',
                 'ORCL', 'ORLY', 'OXY', 'PAYX', 'PBCT', 'PBI', 'PCAR', 'PCG',
                 'PCL', 'PCLN', 'PCP', 'PDCO', 'PEG', 'PEP', 'PETM', 'PFE',
                 'PFG', 'PG', 'PGR', 'PH', 'PHM', 'PKI', 'PLD', 'PLL', 'PM',
                 'PNC', 'PNR', 'PNW', 'POM', 'PPG', 'PPL', 'PRGO', 'PRU',
                 'PSA', 'PSX', 'PVH', 'PWR', 'PX', 'PXD', 'QCOM', 'QEP', 'R',
                 'RAI', 'RDC', 'REGN', 'RF', 'RHI', 'RHT', 'RIG', 'RL', 'ROK',
                 'ROP', 'ROST', 'RRC', 'RSG', 'RTN', 'SBUX', 'SCG', 'SCHW',
                 'SE', 'SEE', 'SHW', 'SIAL', 'SJM', 'SLB', 'SNA', 'SNDK',
                 'SNI', 'SO', 'SPG', 'SPLS', 'SRCL', 'SRE', 'STI', 'STJ',
                 'STT', 'STX', 'STZ', 'SWK', 'SWN', 'SWY', 'SYK', 'SYMC',
                 'SYY', 'T', 'TAP', 'TDC', 'TE', 'TEG', 'TEL', 'TGT', 'THC',
                 'TIF', 'TJX', 'TMK', 'TMO', 'TRIP', 'TROW', 'TRV', 'TSCO',
                 'TSN', 'TSO', 'TSS', 'TWC', 'TWX', 'TXN', 'TXT', 'TYC', 'UA',
                 'UNH', 'UNM', 'UNP', 'UPS', 'URBN', 'USB', 'UTX', 'V', 'VAR',
                 'VFC', 'VIAB', 'VLO', 'VMC', 'VNO', 'VRSN', 'VRTX', 'VTR',
                 'VZ', 'WAG', 'WAT', 'WDC', 'WEC', 'WFC', 'WFM', 'WHR', 'WIN',
                 'WLP', 'WM', 'WMB', 'WMT', 'WU', 'WY', 'WYN', 'WYNN', 'XEC',
                 'XEL', 'XL', 'XLNX', 'XOM', 'XRAY', 'XRX', 'XYL', 'YHOO',
                 'YUM', 'ZION', 'ZMH', 'ZTS')

symbols_other = ('ARLP', 'BREW', 'CHL', 'DECK', 'IACI', 'ILMN', 'MKL', 'MLNX',
                 'SDRL', 'SWKS', 'TSLA', 'UBS')

symbols = symbols_sp500 + symbols_other


def find_names():
    sym_to_name = {sym: None for sym in symbols}

    for sym in symbols:
        try:
            print sym
            html = requests.get(
                'https://finance.yahoo.com/q?s={}'.format(sym)).text
            soup = BeautifulSoup(''.join(html.splitlines()))
            tt = soup.find(attrs={'class': 'title'})
            company_name = tt.text
            sym_to_name[sym] = company_name
        except Exception as e:
            print e

    print sym_to_name


def find_ciks():
    for sym in symbols:
        if sym in sym_to_ciks:
            print 'Already have cik {} for sym {}'.format(
                sym_to_ciks[sym], sym)
            continue
        try:
            print sym
            html = requests.get(
                'https://finance.yahoo.com/q/sec?s={}+SEC+Filings'.format(sym)).text
            soup = BeautifulSoup(''.join(html.splitlines()))
            tt = soup.find('a', text=re.compile('Full Filing.*'))
            href = tt.parent['href']

            html = requests.get(href).text
            soup = BeautifulSoup(''.join(html.splitlines()))
            tt = soup.find(text='CIK:')
            cik = int(''.join(c for c in tt.next.next.next.text
                              if c in '0123456789'))

            sym_to_ciks[sym] = cik
            print cik
        except Exception as e:
            print e

    with open('sym_to_ciks.py', 'w') as f:
        f.write('sym_to_ciks = {}\n'.format(sym_to_ciks))
        f.write('\n')
        f.write('cik_to_syms = {v: k for k, v in sym_to_ciks.items}\n')
    print 'Wrote sym_to_ciks.py'
