from pricehistory import PriceHistory
import pandas as pd
import numpy as np
import requests
from hassib_api import HassibAPI
from helpers import Helpers
from market import Market
from api import AIM_API


class PortfolioRisk:

    # def __init__(self):
    api = AIM_API()

    @staticmethod
    def market_index():
        index_url = 'http://old.tsetmc.com/tsev2/chart/data/Index.aspx?i=32097828799138957&t=value'
        res = requests.get(index_url)
        rows = res.text.split(';')
        index_data = []
        for row in rows:
            index_data.append(row.split(','))
        index_df = pd.DataFrame(index_data, columns=['date', 'index'])
        index_df['date'] = index_df['date'].apply(lambda x: str(x).replace('/', ''))
        index_df = index_df[['date', 'index']]
        index_df['index_return'] = index_df['index'].astype(float).pct_change()
        index_df = index_df[~index_df['index_return'].isna()]
        index_df['date'] = index_df['date'].astype(str)
        index_df.reset_index(inplace=True)
        index_df = index_df[['date', 'index_return']]
        return index_df
    

    @staticmethod
    def stock_price_history(symbols):
        stock_price_history_json = PriceHistory.get(symbols=symbols, is_option=False)
        stock_price_history_df = pd.DataFrame(stock_price_history_json)
        stock_price_history_df = stock_price_history_df[['symbol', 'jdate', 'ret']]
        stock_price_history_df.columns = ['symbol', 'date', 'return']
        stock_price_history_df['return'] -= 1
        return stock_price_history_df
    

    @classmethod
    def std(cls, from_date, symbols=None):
        price_history_df = cls.stock_price_history(symbols=symbols)
        filtered_data = price_history_df[price_history_df['date'] > from_date]
        volatility_df = filtered_data.groupby('symbol')['return'].std().reset_index()
        volatility_df.columns = ['symbol', 'std']
        return volatility_df
    
    
    @classmethod
    def portfolio_std(cls, portfolio, from_date):
        temp_portfo = portfolio.copy()
        temp_portfo['weight'] = temp_portfo['value'] / temp_portfo['value'].sum()
        temp_portfo[['symbol', 'weight']]
        symbols = list(temp_portfo['symbol'].unique())

        std_df = cls.std(from_date=from_date, symbols=symbols)
        merged_df = pd.merge(temp_portfo[['symbol', 'weight']], std_df, how='left', on='symbol')
        merged_df['variance'] = merged_df['std'] ** 2

        weights = merged_df['weight'].values
        variances = merged_df['variance'].values
        n = len(merged_df)
        correlation_matrix = np.identity(n)  # Identity matrix for no correlation
        portfolio_variance = np.dot(weights.T, np.dot(correlation_matrix, weights * variances))
        portfolio_std = np.sqrt(portfolio_variance)
        return portfolio_std


    @classmethod
    def beta(cls, from_date, symbols=None):
        index_return_df = cls.market_index()
        index_return_df = index_return_df[index_return_df['date'] > from_date]
        stock_return_df = cls.stock_price_history(symbols=symbols)
        stock_return_df = stock_return_df[stock_return_df['date'] > from_date]

        market_variance = index_return_df['index_return'].var()
        merged_df = pd.merge(stock_return_df, index_return_df, how='left', on='date')

        beta_df = merged_df.groupby('symbol').apply(lambda group: group[['return', 'index_return']].cov().iloc[0, 1] / market_variance).reset_index()
        beta_df.columns = ['symbol', 'beta']
        return beta_df
    

    @staticmethod
    def portfolio_beta(portfolio, from_date):
        temp_portfo = portfolio.copy()
        temp_portfo['weight'] = temp_portfo['value'] / temp_portfo['value'].sum()
        temp_portfo[['symbol', 'weight']]
        symbols = list(temp_portfo['symbol'].unique())

        beta_df = PortfolioRisk.beta(from_date=from_date, symbols=symbols)
        merged_df = pd.merge(temp_portfo[['symbol', 'weight']], beta_df, how='left', on='symbol')
        beta = (merged_df['weight'] * merged_df['beta']).sum()
        return beta


    @classmethod
    def portfolio_VaR(cls, portfolio, confidential_level=.95, timehorizon='W-FRI'):
        temp_portfo = portfolio.copy()
        symbols = list(temp_portfo['symbol'].unique())
        price_history_df = cls.stock_price_history(symbols=symbols)

        # filtering days which any portfolio assets not exist in history data
        asset_count_per_day = price_history_df.groupby('date')['symbol'].nunique()
        valid_dates = asset_count_per_day[asset_count_per_day == len(temp_portfo)].index
        price_history_df = price_history_df[price_history_df['date'].isin(valid_dates)]
        # end filtering

        price_history_df['date'] = price_history_df['date'].apply(Helpers.to_gregorian_date)
        price_history_df['date'] = pd.to_datetime(price_history_df['date'])

        # for daily timehorizon, resampling will not use
        if timehorizon != 'd':
            price_history_df = price_history_df.set_index('date')
            price_history_df = price_history_df.groupby('symbol')['return'].resample(timehorizon).sum().reset_index()

        price_history_df = pd.merge(price_history_df, temp_portfo[['symbol', 'weight']], how='left', on='symbol')
        price_history_df['weighted_return'] = price_history_df['return'] * price_history_df['weight']
        portfolio_historical_return = price_history_df.groupby('date')['weighted_return'].sum()
        portfolio_historical_return = portfolio_historical_return.reset_index()
        portfolio_historical_return.columns = ['date', 'return']
       
        total_len = len(portfolio_historical_return)
        temp = portfolio_historical_return.sort_values('return').iloc[:int((1-confidential_level)*total_len)]
        VaR = temp.iloc[-1]['return']
        cVaR = temp['return'].mean()
        return {'VaR': VaR, 'cVaR': cVaR}
    
    
    @staticmethod
    def portfolio_cc_underlyings_weight(cc_portfo, top_n=10):
        temp_portfo = cc_portfo.copy()
        temp_portfo['strategy_value'] = (temp_portfo['spot_price'] - temp_portfo['price']) * temp_portfo['quantity'] * temp_portfo['size']
        uas_weight = temp_portfo.groupby('spot')['strategy_value'].sum().reset_index()
        uas_weight.columns = ['underlying', 'strategy_value']
        uas_weight['weight'] = uas_weight['strategy_value'] / uas_weight['strategy_value'].sum()
        uas_weight = uas_weight.sort_values('weight', ascending=False)
        uas_weight = uas_weight.iloc[:top_n]
        return uas_weight
    

    @staticmethod
    def portfolio_cc_contracts_weight(cc_portfo, top_n=10):
        temp_portfo = cc_portfo.copy()
        temp_portfo['strategy_value'] = (temp_portfo['spot_price'] - temp_portfo['price']) * temp_portfo['quantity'] * temp_portfo['size']
        temp_portfo['weight'] = temp_portfo['strategy_value'] / temp_portfo['strategy_value'].sum()
        contracts_weight = temp_portfo[['symbol', 'strategy_value', 'weight']]
        contracts_weight = contracts_weight.sort_values('weight', ascending=False)
        contracts_weight = contracts_weight.iloc[:top_n]
        return contracts_weight


    @staticmethod
    def portfolio_cc_ttm(cc_portfo):
        temp_portfo = cc_portfo.copy()
        temp_portfo['gdue_date'] = temp_portfo['due_date'].apply(Helpers.to_gregorian_date)
        temp_portfo['ttm'] = temp_portfo.apply(lambda x: Helpers.cal_ttm(x['gdue_date'], Helpers.to_gregorian_date(x['date'])), axis=1)
        temp_portfo['strategy_value'] = (temp_portfo['spot_price'] - temp_portfo['price']) * temp_portfo['quantity'] * temp_portfo['size']
        temp_portfo['weight'] = temp_portfo['strategy_value'] / temp_portfo['strategy_value'].sum()
        pttm = (temp_portfo['ttm'] * temp_portfo['weight']).sum()
        return pttm


    @staticmethod
    def portfolio_cc_min_ttm_list(cc_portfo, ttm_thershold=2):
        temp_portfo = cc_portfo.copy()
        temp_portfo['gdue_date'] = temp_portfo['due_date'].apply(Helpers.to_gregorian_date)
        temp_portfo['ttm'] = temp_portfo.apply(lambda x: Helpers.cal_ttm(x['gdue_date'], Helpers.to_gregorian_date(x['date'])), axis=1)
        temp_portfo['strategy_value'] = (temp_portfo['spot_price'] - temp_portfo['price']) * temp_portfo['quantity'] * temp_portfo['size']
        temp_portfo['rcut'] = temp_portfo['strike'] / temp_portfo['spot_price'] - 1
        filtered_portfolio = temp_portfo[temp_portfo['ttm'] <= ttm_thershold]
        filtered_portfolio = filtered_portfolio[['symbol', 'quantity', 'strategy_value', 'ttm', 'rcut']]
        return filtered_portfolio

    
    @staticmethod
    def portfolio_cc_rcut(cc_portfo):
        temp_portfo = cc_portfo.copy()
        temp_portfo['strategy_value'] = (temp_portfo['spot_price'] - temp_portfo['price']) * temp_portfo['quantity'] * temp_portfo['size']
        temp_portfo['weight'] = temp_portfo['strategy_value'] / temp_portfo['strategy_value'].sum()
        temp_portfo['rcut'] = temp_portfo['strike'] / temp_portfo['spot_price'] - 1
        p_rcut = (temp_portfo['rcut'] * temp_portfo['weight']).sum()
        return p_rcut


    @staticmethod
    def portfolio_cc_min_rcut_list(cc_portfo, rcut_thershold=-.1):
        temp_portfo = cc_portfo.copy()
        temp_portfo['rcut'] = temp_portfo['strike'] / temp_portfo['spot_price'] - 1
        temp_portfo['gdue_date'] = temp_portfo['due_date'].apply(Helpers.to_gregorian_date)
        temp_portfo['ttm'] = temp_portfo.apply(lambda x: Helpers.cal_ttm(x['gdue_date'], Helpers.to_gregorian_date(x['date'])), axis=1)
        temp_portfo['strategy_value'] = (temp_portfo['spot_price'] - temp_portfo['price']) * temp_portfo['quantity'] * temp_portfo['size']
        filtered_portfolio = temp_portfo[temp_portfo['rcut'] >= rcut_thershold]
        filtered_portfolio = filtered_portfolio[['symbol', 'quantity', 'strategy_value', 'ttm', 'rcut']]
        return filtered_portfolio


    @staticmethod
    def portfolio_cc_unbalance(cc_portfolio_option, cc_portfolio_stock):
        temp_option_portfo = cc_portfolio_option.copy()
        temp_stock_portfo = cc_portfolio_stock.copy()
        temp_stock_portfo['ua_q_cum'] = temp_stock_portfo.groupby('symbol')['quantity'].transform(sum)
        temp_option_portfo['op_q_cum'] = temp_option_portfo.groupby('spot')['quantity'].transform(sum)
        cc_portfolio_stock_cumulative = temp_stock_portfo.drop_duplicates(subset='symbol')
        cc_portfo_cumulative = temp_option_portfo.drop_duplicates(subset='spot')

        cc_portfolio_stock_cumulative = cc_portfolio_stock_cumulative[['symbol', 'ua_q_cum']]
        cc_portfo_cumulative = cc_portfo_cumulative[['spot', 'size', 'op_q_cum']]

        cc_unbalance = pd.merge(cc_portfo_cumulative, cc_portfolio_stock_cumulative, how='left', left_on='spot', right_on='symbol')[['spot', 'size', 'op_q_cum', 'ua_q_cum']]
        cc_unbalance.columns = ['underlying', 'size', 'op_q', 'ua_q']
        cc_unbalance['op_at_size'] = cc_unbalance['op_q'] * cc_unbalance['size']
        cc_unbalance['unbalance'] = cc_unbalance['op_at_size'] - cc_unbalance['ua_q']
        cc_unbalance = cc_unbalance[['underlying', 'unbalance']]
        cc_unbalance = cc_unbalance[cc_unbalance['unbalance'] != 0]
        return cc_unbalance
    

    @staticmethod
    def portfolio_fund_values(owner, report_date):
        owner = owner
        report_date = report_date
        total_portfolio_cfd = HassibAPI.get_portfo_cfd(owner=owner, date=report_date)
        total_portfolio_crypto = HassibAPI.get_portfo_crypto(owner=owner, date=report_date)
        total_portfolio_future = HassibAPI.get_portfo_future(owner=owner, date=report_date)
        total_portfolio_investment = HassibAPI.get_portfo_investment(owner=owner, date=report_date)
        total_portfolio_option = HassibAPI.get_portfo_option(owner=owner, date=report_date)
        total_portfolio_stock = HassibAPI.get_portfo_stock(owner=owner, date=report_date)
        total_portfolio = pd.concat([total_portfolio_cfd, total_portfolio_crypto, total_portfolio_future, total_portfolio_investment, total_portfolio_option, total_portfolio_stock])
        total_portfolio_value_df = total_portfolio.groupby('fund')['value'].sum().reset_index()
        total_portfolio_value_df['weight'] = total_portfolio_value_df['value'] / total_portfolio_value_df['value'].sum()
        return total_portfolio_value_df


    # @staticmethod
    # def create_fof(owner, date):
    #     portfo1 = HassibAPI.get_portfo_stock(owner=owner, date=date)
    #     portfo2 = HassibAPI.get_portfo_option(owner=owner, date=date)
    #     portfo3 = HassibAPI.get_portfo_cfd(owner=owner, date=date)
    #     portfo4 = HassibAPI.get_portfo_crypto(owner=owner, date=date)
    #     portfo5 = HassibAPI.get_portfo_future(owner=owner, date=date)
    #     portfo6 = HassibAPI.get_portfo_investment(owner=owner, date=date)

    #     # future size specification
    #     if len(portfo5):
    #         portfo5.loc[portfo5['symbol'].str.contains('GB'), 'size'] = 1
    #         portfo5.loc[portfo5['symbol'].str.contains('KB'), 'size'] = 1000
    #         portfo5.loc[portfo5['symbol'].str.contains('ETC'), 'size'] = 1000
    #         portfo5.loc[portfo5['symbol'].str.contains('JZ'), 'size'] = 1000
    #         portfo5.loc[portfo5['symbol'].str.contains('SIL'), 'size'] = 10
    #         portfo5.loc[portfo5['symbol'].str.contains('SAF'), 'size'] = 100

    #         portfo5['value'] = portfo5['margin'] * portfo5['quantity'] * portfo5['size']
    #     # end

    #     fof = pd.concat([portfo1 ,portfo2, portfo3, portfo4, portfo5, portfo6])

    #     # find GOLD and SAFRAN in stock portfolio (portfo1)
    #     gold_funds_list = ['کهربا', 'عیار', 'جواهر', 'آلتون', 'طلا', 'زر', 'ناب', 'درخشان', 'زرفام', 'لیان', 'زرفام', 'گنج', 'مثقال', 'زروان', 'نفیس', 'گوهر', 'تابش', 'آتش']
    #     safran_funds_list = ['نهال', 'سحرخیز']
    #     fof.loc[fof['symbol'].isin(gold_funds_list), 'fund'] = 'Gold'
    #     fof.loc[fof['symbol'].isin(safran_funds_list), 'fund'] = 'Safran'
    #     # end
        
    #     # fof funds separation
    #     equity_fund = fof[fof['fund'].str.contains('Equity')]
    #     fixed_fund = fof[fof['fund'].str.contains('Fixed')]
    #     crypto_fund = fof[fof['fund'].str.contains('Crypto')]
    #     usd_fund = fof[fof['fund'].str.contains('USD')]
    #     gold_fund = fof[fof['fund'].str.contains('Gold')]
    #     safran_fund = fof[fof['fund'].str.contains('Safran')]        
    #     # end

    #     # set tag fo fof funds
    #     equity_fund['fof_fund'] = 'Equity'
    #     fixed_fund['fof_fund'] = 'Fixed'
    #     crypto_fund['fof_fund'] = 'Crypto'
    #     usd_fund['fof_fund'] = 'USD'
    #     gold_fund['fof_fund'] = 'Gold'
    #     safran_fund['fof_fund'] = 'Safran'
    #     # end

    #     fof = pd.concat([equity_fund, fixed_fund, crypto_fund, usd_fund, gold_fund, safran_fund])
    #     return fof


    # @classmethod
    # def fof_funds_weight(cls, owner, date):
    #     temp_fof = cls.create_fof(owner=owner, date=date)
    #     fof_weigh_df = temp_fof.groupby('fof_fund')['value'].sum().reset_index()
    #     fof_weigh_df['weight'] = fof_weigh_df['value'] / fof_weigh_df['value'].sum()
    #     fof_weigh_df = fof_weigh_df.sort_values('weight', ascending=False)
    #     return fof_weigh_df


    
    @classmethod
    def get_owner_funds_list(cls):
        owner_fund_list = cls.api.get_funds()
        owner_fund_list = list(owner_fund_list[owner_fund_list['title'].str.endswith('_Fund')]['title'].values)
        owner_fund_list.sort()
        owner_fund_list.insert(0, 'FOF')
        return owner_fund_list


    @classmethod
    def get_ownership(cls, date, owner_fund):
        ownerships = cls.api.get_ownership(date=date, owner_fund=owner_fund)
        ownerships = ownerships[['date', 'owner', 'fund', 'net_unit']]
        ownerships.columns = ['date', 'owner', 'fund', 'ownership_nu']
        return ownerships


    @classmethod
    def fof_weights(cls, date, owner_fund):
        fund_properties_df = cls.api.get_fund_properties(date=date, fund=owner_fund)
        ownerships_df = cls.get_ownership(date=date, owner_fund=owner_fund)

        merged_df = pd.merge(ownerships_df, fund_properties_df, left_on='owner', right_on='fund', how='left')
        merged_df = merged_df[['date_x', 'owner', 'fund_x', 'ownership_nu', 'nu', 'nav']]
        merged_df.columns = ['date', 'owner', 'fund', 'ownership_nu', 'fund_nu', 'nav']

        merged_df['ownership_value'] = merged_df['ownership_nu'] * merged_df['nav']
        merged_df['fund_value'] = merged_df['fund_nu'] * merged_df['nav']

        merged_df = merged_df[['owner', 'fund', 'ownership_value', 'fund_value']]

        base_name = owner_fund.replace('Fund', '')

        merged_df['sub_fund'] = merged_df['fund'].replace(rf'{base_name}', '', regex=True)
        merged_df = merged_df[['owner', 'sub_fund', 'ownership_value']]
        merged_df = merged_df.groupby('sub_fund')['ownership_value'].sum().reset_index()
        merged_df['weight'] = merged_df['ownership_value'] / merged_df['ownership_value'].sum()

        return merged_df