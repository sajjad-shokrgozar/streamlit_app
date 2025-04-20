import pandas as pd
import requests
from typing import List, Union, Optional
from arabic_replace import Arabic_to_Persian, Persian_to_Arabic

class info:
    def __init__(self, data: dict):
        self.reference_id = data['reference_id']
        self.symbol = data['symbol']
        self.name = data['name']
        self.paper_type = data['paper_type']
        self.market_type = data['market_type']
        self.market_name = data['market_name']
        self.market_key = data['market_key']
        self.underlying_asset = data['underlying_asset']
        self.option_contracts = data['option_contracts']
        self.future_contracts = data['future_contracts']
        self.contract_type = data['contract_type']
        self.end_date = data['end_date']
        self.strike_price = data['strike_price']
        self.industry_name = data['industry_name']
        self.industry_key = data['industry_key']
        self.sub_industry_name = data['sub_industry_name']
        self.sub_industry_key = data['sub_industry_key']
        self.open_contracts = data['open_contracts']
        self.size = data['size']
        self.fee =  self._fee(buy_fee=data['fee']['buy_fee'],
                              sell_fee=data['fee']['sell_fee'],
                              long_settlement_fee=data['fee']['long_settlement_fee'],
                              short_settlement_fee=data['fee']['short_settlement_fee'],
                              storage_fee=data['fee']['storage_fee'])

    class _fee:
        def __init__(self, buy_fee, sell_fee, long_settlement_fee, short_settlement_fee, storage_fee):
            self.buy_fee = buy_fee
            self.sell_fee = sell_fee
            self.long_settlement_fee = long_settlement_fee
            self.short_settlement_fee = short_settlement_fee
            self.storage_fee = storage_fee

class API:
    @staticmethod
    def make_url(main_url, filters: dict):
        for key, value in filters.items():
            if value is not None:
                main_url += f'{key}={value}&'
        return main_url

    @staticmethod
    def parsed_data(res: dict, params: dict):
        def get(res: dict, depth: list):
            try:
                if len(depth) == 1:
                    return res[depth[0]]
            except:
                return None
            return get(res=res[depth[0]], depth=depth[1:])

        df = pd.DataFrame()
        for col, depth in params.items():
            df[col] = [get(res=x, depth=depth) for x in res]
        return df

    def fetch(self, url: str, params: dict, method: str = 'GET', check_next_page: bool = False):
        if method == 'GET':
            res = requests.get(url).json()['results']
        else:  # method == 'POT'
            res = requests.post(url).json()['results']

        parsed = self.parsed_data(res=res, params=params)
        if check_next_page:
            return parsed, res['has_next']
        return parsed

class AIM_API(API):
    def __init__(self):
        super().__init__()
        # self.IM_url = 'http://192.168.60.130:8002'
        # self.AM_url = 'http://192.168.60.130:8001'

        self.IM_url = 'http://5.160.13.220:8002'
        self.AM_url = 'http://5.160.13.220:8001'

    def get_funds(self):
        res = requests.get(self.IM_url + '/fund/get_funds/').json()['results']
        df = pd.DataFrame.from_dict(res)
        df.drop(columns=['is_enabled'], inplace=True)
        return df

    def get_accounts(self):
        res = requests.get(self.IM_url + '/account/get_accounts/').json()['results']

        df = pd.DataFrame()
        df['id'] = [int(x['uid']) for x in res]
        df['owner'] = [x['owner'] for x in res]
        df['broker'] = [x['broker'] for x in res]
        df['description'] = [x['description'] for x in res]
        funds = []
        for x in res:
            fund = ''
            for y in x['funds']:
                fund += y['title'] + ','

            funds.append(fund if fund == '' else fund[:-1])
        df['funds'] = funds

        return df
    def get_customers(self):
        res = requests.get(self.IM_url + '/base/get_customers/').json()['results']
        df = pd.DataFrame.from_dict(res)

        return df

    def get_ownership(self, date: str = None, fund: str = None, owner_person: str = None, owner_fund: str = None,
                      automatic: bool = None):
        if owner_person is not None:
            temp = self.get_customers()
            owner_person = temp[temp.english_name == owner_person].uid.values[0]

        url = self.make_url(main_url=self.IM_url + '/base/get_ownerships/?',
                            filters={'date__date': date,
                                     'owner_fund__title': owner_fund,
                                     'owner_customer__uid': owner_person,
                                     'fund__title': fund,
                                     'automatic': automatic})
        params = {'date': ['date'],
                  'owner_fund': ['owner_fund', 'title'],
                  'owner_person': ['owner_customer', 'english_name'],
                  'fund': ['fund', 'title'],
                  'fund_flow_unit': ['fund_flow_unit'],
                  'management_fee_unit': ['management_fee_unit'],
                  'performance_fee_unit': ['performance_fee_unit'],
                  'settlement_unit': ['settlement_unit'],
                  'net_unit': ['net_unit']}

        df = self.fetch(url=url, params=params, method='GET')
        df.insert(1, 'owner',
                  [(df.owner_fund[i] if df.owner_fund[i] is not None else df.owner_person[i]) for i in df.index])
        df.drop(columns=['owner_fund', 'owner_person'], inplace=True)
        return df

    def get_symbols(self, search: str = None):
        url = self.make_url(main_url=self.AM_url + '/base/get_symbols/?',
                            filters={'search': search})

        params = {'symbol': ['title'],
                  'name': ['name']}
        return self.fetch(url=url, params=params, method='GET')

    def get_cash_flow(self, date: str = None, fund: str = None):
        url = self.make_url(main_url=self.IM_url + '/base/get_cash_flows/?',
                            filters={'date__date': date,
                                     'fund__title': fund})
        params = {'date': ['date'],
                  'fund': ['fund', 'title'],
                  'account_id': ['account', 'uid'],
                  'account': ['account', 'owner'],
                  'broker': ['account', 'broker'],
                  'flow': ['flow'],
                  'description': ['description']}
        return self.fetch(url=url, params=params, method='GET')

    def get_fund_properties(self, date: str = None, fund: str = None):
        url = self.make_url(main_url=self.IM_url + '/fund/get_fund_properties/?',
                            filters={'date__date': date,
                                     'fund__title': fund})

        params = {'date': ['date'],
                  'fund': ['fund', 'title'],
                  'asset': ['asset'],
                  'margin': ['margin'],
                  'cash': ['cash'],
                  'receivable': ['receivable'],
                  'nu': ['nu'],
                  'nav': ['nav']}
        return self.fetch(url=url, params=params, method='GET')

    def get_cash_accounts(self, date: str = None):
        url = self.make_url(main_url=self.IM_url + '/account/get_cash_accounts/?',
                            filters={'date__date': date})
        params = {'date': ['date'],
                  'account_id': ['account', 'uid'],
                  'owner': ['account', 'owner'],
                  'broker': ['account', 'broker'],
                  'cash': ['cash']}
        return self.fetch(url=url, params=params, method='GET')

    def get_credit_account_assign(self):
        url = self.make_url(main_url=self.IM_url + '/account/get_credit_account_assigns/?',
                            filters={})
        params = {'account_id': ['account', 'uid'],
                  'owner': ['account', 'owner'],
                  'broker': ['account', 'broker'],
                  'fund': ['fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_fund_flows(self, date: str = None, person_owner: str = None, fund_owner: str = None,
                       receiving_fund: str = None, account: str = None) -> pd.DataFrame:
        url = self.make_url(main_url=self.IM_url + '/fund/get_fund_flows/?',
                            filters={'date__date': date,
                                     'customer_owner__english_name': person_owner,
                                     'customer_fund__title': fund_owner,
                                     'receiving_fund__title': receiving_fund,
                                     'account__uid': account})
        params = {'date': ['date'],
                  'owner_fund': ['customer_fund', 'title'],
                  'owner_person': ['customer_owner', 'english_name'],
                  'receiving_fund': ['receiving_fund', 'title'],
                  'account_id': ['account', 'uid'],
                  'account': ['account', 'owner'],
                  'broker': ['account', 'broker'],
                  'type': ['type'],
                  'flow': ['flow'],
                  'description': ['description'],
                  'unit_type': ['unit_type']}
        df = self.fetch(url=url, params=params, method='GET')
        df.insert(1, 'owner',
                  [(df.owner_fund[i] if df.owner_fund[i] is not None else df.owner_person[i]) for i in df.index])
        df.drop(columns=['owner_fund', 'owner_person'], inplace=True)
        return df

    def get_portfo_stock(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/stock/get_portfolios/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}

        return self.fetch(url=url, params=params, method='GET')

    def get_trade_stock(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/stock/get_trades/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'side': ['side'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'value': ['value'],
                  'fee': ['fee'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_movement_stock(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/stock/get_movements/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'from_fund': ['fund', 'title'],
                  'to_fund': ['assign_fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_portfo_option(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/option/get_portfolios/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'position': ['position'],
                  'contract': ['contract'],
                  'quantity': ['quantity'],
                  'size': ['size'],
                  'price': ['price'],
                  'strike': ['strike'],
                  'margin': ['margin'],
                  'due_date': ['due_date'],
                  'spot': ['spot'],
                  'spot_price': ['spot_price'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_trade_option(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/option/get_trades/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'side': ['side'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_movement_option(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/option/get_movements/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'position': ['position'],
                  'contract': ['contract'],
                  'quantity': ['quantity'],
                  'size': ['size'],
                  'price': ['price'],
                  'strike': ['strike'],
                  'margin': ['margin'],
                  'due_date': ['due_date'],
                  'spot': ['spot'],
                  'spot_price': ['spot_price'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'from_fund': ['fund', 'title'],
                  'to_fund': ['assign_fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_portfo_future(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/future/get_portfolios/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'name': ['name'],
                  'price': ['price'],
                  'margin': ['margin'],
                  'position': ['position'],
                  'quantity': ['quantity'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title'], }
        return self.fetch(url=url, params=params, method='GET')

    def get_trade_future(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/future/get_trades/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'name': ['name'],
                  'side': ['side'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'fee': ['fee'],
                  'fund': ['fund', 'title'],
                  'broker': ['broker'],
                  'owner': ['owner']}
        return self.fetch(url=url, params=params, method='GET')

    # def get_movement_future(self, date: str = None, owner: str = None, broker: str = None): # todo
    #     url = self.make_url(main_url=self.AM_url + '/future/get_movements/?',
    #                         filters={'date': date,
    #                                  'owner': owner,
    #                                  'broker': broker})
    #     return requests.get(url).json()['results'][0]

    def get_portfo_investment(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/investment/get_portfolios/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'quantity': ['quantity'],
                  'change_quantity': ['change_quantity'],
                  'usd': ['usd'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_trade_investment(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/investment/get_trades/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'quantity': ['quantity'],
                  'side': ['side'],
                  'usd': ['usd'],
                  'value': ['value'],
                  'fee': ['fee'],
                  'fund': ['fund', 'title'],
                  'broker': ['broker'],
                  'owner': ['owner']}
        return self.fetch(url=url, params=params, method='GET')

    def get_movements_investment(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/investment/get_movements/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'quantity': ['quantity'],
                  'usd': ['usd'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'from_fund': ['fund', 'title'],
                  'to_fund': ['assign_fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_portfo_crypto(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/crypto/get_portfolios/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'usd': ['usd'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}

        return self.fetch(url=url, params=params, method='GET')

    def get_portfo_cfd(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/cfd/get_portfolios/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'position': ['position'],
                  'quantity': ['quantity'],
                  'lot': ['lot'],
                  'leverage': ['leverage'],
                  'price': ['price'],
                  'margin': ['margin'],
                  'usd': ['usd'],
                  'value': ['value'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'fund': ['fund', 'title']}
        return self.fetch(url=url, params=params, method='GET')

    def get_trade_cfd(self, date: str = None, owner: str = None, broker: str = None):
        url = self.make_url(main_url=self.AM_url + '/cfd/get_trades/?',
                            filters={'date': date,
                                     'owner': owner,
                                     'broker': broker})

        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'side': ['side'],
                  'quantity': ['quantity'],
                  'price': ['price'],
                  'lot': ['lot'],
                  'leverage': ['leverage'],
                  'usd': ['usd'],
                  'fund': ['fund', 'title'],
                  'broker': ['broker'],
                  'owner': ['owner']}
        return self.fetch(url=url, params=params, method='GET')

    def get_active_days(self):
        url = self.make_url(main_url=self.AM_url + '/base/get_active_days/', filters={})
        params = {'date': ['date'],
                  'day_week': ['day_week'],
                  'yesterday': ['previous_day_date'],
                  'day_interval': ['day_interval'],
                  'USD': ['usd']}
        return  self.fetch(url=url, params=params, method='GET')

    # def get_movement_cfd(self, date: str = None, owner: str = None, broker: str = None): # todo
    #     url = self.make_url(main_url=self.AM_url + '/cfd/get_movements/?',
    #                         filters={'date': date,
    #                                  'owner': owner,
    #                                  'broker': broker})
    #     return requests.get(url).json()['results'][0]
    # return requests.get(url).json()['results'][0]

    def create_cash_account(self, date: str, cash_dict: dict):
        data = {'date': date, 'cash_accounts': []}
        for account_uid, cash in cash_dict.items():
            data['cash_accounts'].append({'account_uid': account_uid, '_comment': '', 'cash': cash})
        return requests.post(self.IM_url + '/account/update_or_create_list_cash_account/', json=data).json()

    def calculate_cash_flow(self, date: str):
        res = requests.post(self.IM_url + '/base/calculate_cash_flow/', json={'date': str(date)}).json()
        if res['status'] == 'success':
            return "ok"
        return

    def account_credit_settlement(self, date: str):
        return requests.post(self.IM_url + '/fund/account_credit_settlement/', json={'date': str(date)}).json()

    def calculate_unbalancing_cash_account(self, date: str):
        return requests.post(self.IM_url + '/account/calculate_unbalancing_cash_account/',
                             json={'date': str(date)}
                             ).json()

    def calculate_fund_properties(self, date: str):
        return requests.post(self.IM_url + '/fund/calculate_fund_properties/', json={'date': str(date)}).json()

    def fund_cash_settlement(self, date: str, funds: list):
        return requests.post(self.IM_url + '/fund/fund_cash_settlement/',
                             json={'date': str(date), "fund_titles": funds}
                             ).json()

    def update_portfo_data(self, date: str):
        return requests.post(self.AM_url + '/base/update_portfo_data/',
                             json={'date': str(date)}
                             ).json()['status']

    def get_turnovers(self, date: str):
        url = self.make_url(main_url=self.AM_url + '/base/get_trade_turnovers/?',
                            filters={})
        params = {'date': ['date'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'detail': ['turnover_detail'],
                  'value': ['value']}
        df = self.fetch(url=url, params=params, method='GET')
        df = df[df.date == date].reset_index(drop=True)
        df['value'] = df.value.apply(lambda x: f"{x:,.0f}")
        return df

    def get_fee_unit_changes(self, date: str = None, customer: str = None, fund: str = None, label: str = None):
        url = self.make_url(main_url=self.IM_url + '/base/get_fee_unit_changes/?',
                            filters={'date__date': date, 'customer__english_name': customer, 'fund__title': fund,
                                     'label': label})

        params = {'date': ['date'],
                  'customer': ['customer', 'english_name'],
                  'fund': ['fund', 'title'],
                  'unit_change': ['unit_change'],
                  'value': ['value'],
                  'label': ['label']}

        return self.fetch(url=url, params=params, method='GET')

    def get_rates(self, date: str = None, customer: str = None, fund: str = None):
        url = self.make_url(main_url=self.IM_url + '/base/get_rates/?',
                            filters={'date__date': date, 'customer__english_name': customer, 'fund__title': fund})
        params = {'date': ['date'],
                  'customer': ['customer', 'english_name'],
                  'fund': ['fund', 'title'],
                  'irr': ['irr_yearly'],
                  'r_performance': ['r_performance']}

        return self.fetch(url=url, params=params, method='GET')

    def get_derivatives_accounting(self, date: str = None):
        url = self.make_url(main_url=self.IM_url + '/base/get_derivatives_accounting/?',
                            filters={'date__date': date})
        params = {'date': ['date'],
                  'symbol': ['symbol'],
                  'broker': ['broker'],
                  'owner': ['owner'],
                  'description': ['description'],
                  'value': ['value']}
        return self.fetch(url=url, params=params, method='GET')

class Database_API(API):
    def __init__(self):
        super().__init__()
        # self.url = 'http://192.168.60.130:8004/'
        self.url = 'http://5.160.13.220:8000'

    def get_info_list(self, paper_type: str = None, market_type: str = None, search: str = None,
                      limit: int = 10, page: int = 1):
        """
        :param paper_type: stock, rights, bond, option, future, certificate, fund
        :param market_type: bourse, fara_bourse, commodity
        :return:
        """

        url = self.make_url(main_url=self.url + '/asset/get_assets/?',
                            filters={'limit': limit,
                                     'page': page,
                                     'paper_type': paper_type,
                                     'market_type': market_type,
                                     'search': search})
        res = requests.get(url).json()
        data: List[dict] = res['results']
        has_next = res['has_next']

        result: List[info] = []

        for x in data:
            result.append(info(data=x))
        return result, has_next

    def get_info(self, by_reference_id: str = None, by_symbol: str = None, by_name: str = None) -> info:
        def error_func(by_reference_id, by_symbol, by_name):
            error = f"by_reference_id:{by_reference_id} by_symbol:{by_symbol} by_name:{by_name} Not Fund"
            raise error

        def search_by(by_value: str, by_what: str, error: callable) -> Optional[info]:
            page = 1
            has_next = True
            while has_next:
                objs, has_next = self.get_info_list(page=page, search=by_value)
                for obj in objs:
                    if Arabic_to_Persian(getattr(obj, by_what)) == Arabic_to_Persian(by_value):
                        return obj
                page += 1
            return error()

        err = lambda: error_func(by_reference_id, by_symbol, by_name)

        if by_reference_id is not None:
            url = self.make_url(main_url=self.url + f'/asset/{by_reference_id}/get_asset/',
                                filters={})
            data = requests.get(url).json()
            return info(data=data)

        if by_symbol is not None:
            return search_by(by_value=by_symbol, by_what='symbol', error=err)

        if by_name is not None:
            return search_by(by_value=by_name, by_what='name', error=err)

        return err()
