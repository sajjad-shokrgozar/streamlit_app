import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from report import PortfolioRisk
from hassib_api import HassibAPI
# from helpers import Helpers
import matplotlib.pyplot as plt
import os
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# Set wide layout
st.set_page_config(page_title="Portfolios Report", layout="wide")

# ************************************************************************************************************************************
# --------------------------------------------------------------- CONFIGS -------------------------------------------------------
# ************************************************************************************************************************************

# This should be on top of your script
cookies = EncryptedCookieManager(
    prefix="ktosiek/streamlit-cookies-manager/",
    password=os.environ.get("COOKIES_PASSWORD", "mycomplex741@&"),
)

users_db = {
    'manager': {'password': 'qwe', 'role': 'manager'},
    'guest': {'password': 'asd', 'role': 'guest'},
    'sajjad': {'password': '123', 'role': 'trader'},
    'akbar': {'password': '456', 'role': 'trader'},
}




# ************************************************************************************************************************************
# --------------------------------------------------------------- ACCOUNT, DATE SELECTION -------------------------------------------------------
# ************************************************************************************************************************************
# Check if the cookies are ready
if not cookies.ready():
    st.stop()

# Helper function to login the user and check their credentials
def login_user(username, password):
    user = users_db.get(username)
    if user and user['password'] == password:
        return user['role']
    return None

# Check if the user is logged in by looking for a cookie
logged_in = cookies.get("logged_in", "False") == "True"  # Convert cookie string back to boolean

if not logged_in:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        role = login_user(username, password)
        if role:
            # Set a cookie indicating the user is logged in and store the user role
            cookies["logged_in"] = "True"
            cookies["username"] = username
            cookies["role"] = role
            cookies.save()  # Save the cookies and trigger a rerun
            st.success("Logged in successfully!")
            st.rerun()  # Rerun the app after login
        else:
            st.error("Invalid credentials")
else:
    username = cookies.get('username')
    role = cookies.get('role')


    report_date_list = list(HassibAPI.get_active_days().sort_values('date', ascending=False)['date'].dropna().values)
    current_report_date = st.query_params.get("date", report_date_list[0])
    
    # Step 1: Simulate account list
    # accounts = ['HojjatShekhAttar', 'ElmGostarPRX', 'Maleki', 'NahidMirzaei',
    #     'MrHeidari', 'Mohaymen', 'AliKarami', 'Madiran', 'MazyarFarokhi',
    #     'HamidAkbari', 'ShahabJavanmardi', 'Hassib', 'MahdiKeshavarz',
    #     'ElmGostar']
    # accounts.sort()
    
    accounts = [
        'FOF',
        'Ali_Karami_Fund',
        'ElmGostar_Fund',
        'Hamid_Akbari_Fund',
        'Hojjat_Attar_Fund',
        'Madiran_Fund',
        'Mahdi_Keshavarz_Fund',
        'Maleki_Fund',
        'Mazyar_Farokhi_Fund',
        'Mohaymen_Fund',
        'Nahid_Mirzaei_Fund',
        'Narges_Darvish_Fund',
        'Shahab_Javanmardi_Fund',
    ]
    accounts.sort()


    # Step 2: Get current owner from query params (default to first account)
    current_owner = st.query_params.get("owner", accounts[0])

    # Step 3: UI - Account Selector
    col1, col2, col3 = st.columns([1, 1, 5])  # 1/6 of the row goes to selectbox
    with col1:
        selected_owner = st.selectbox("Choose an account", options=accounts, index=accounts.index(current_owner))
    with col2:
        selected_report_date = st.selectbox("Choose a date", options=report_date_list, index=report_date_list.index(current_report_date))

    if selected_owner != current_owner or selected_report_date != current_report_date:
        st.query_params["owner"] = selected_owner
        st.query_params["date"] = selected_report_date
        st.rerun()
    with col3:
        # Step 4: Use this selected owner and report_date
        owner = selected_owner
        report_date = selected_report_date
        # st.write("---")
        st.title(f'✅ {owner} - {report_date[:4]}/{report_date[4:6]}/{report_date[6:8]}')

    st.write("---")


    # ************************************************************************************************************************************
    # --------------------------------------------------------------- CALCULATIONS -------------------------------------------------------
    # ************************************************************************************************************************************
    # FOF
    # fof_weights_df = PortfolioRisk.fof_funds_weight(owner=owner, date=report_date)
    # fof_weights_df['weight'] = round(fof_weights_df['weight'] * 100, 1)
    # fof_weights_df['value'] = fof_weights_df['value'] / 1e7
    # fof_weights_df = fof_weights_df.sort_values('value', ascending=False)
    # fof_weights_df['value'] = fof_weights_df['value'].astype(int)
    # fof_weights_df.columns = ['fof_fund', 'value(IRMT)', 'weight(%)']
    # fof_color_mapping = {'Equity': '#FFB6C1', 'Fixed': '#87CEEB', 'Crypto': '#98FF98', 'USD': '#FFDAB9', 'Gold': '#E6E6FA', 'Safran': '#F08080'}
    # fof_colors = [fof_color_mapping.get(fund, '#d3d3d3') for fund in fof_weights_df['fof_fund']]
    # fof_weights_df.reset_index(drop=True, inplace=True)
    # fof_weights_df.index = fof_weights_df.index + 1
    # # portfolio_funds_weight['value(IRMT)'] = portfolio_funds_weight['value(IRMT)'].apply(lambda x: f"{x:,}")

    # fof_weight_fig, ax = plt.subplots()
    # ax.pie(fof_weights_df['weight(%)'], labels=fof_weights_df['fof_fund'], autopct='%1.1f%%', startangle=90, colors=fof_colors)
    # ax.axis('equal')  # Equal aspect ratio ensures pie is circular


    fof_weights_df = PortfolioRisk.fof_weights(date=report_date, owner_fund=owner)
    fof_weights_df['weight'] = round(fof_weights_df['weight'] * 100, 1)
    fof_weights_df['ownership_value'] = fof_weights_df['ownership_value'] / 1e7
    fof_weights_df['ownership_value'] = fof_weights_df['ownership_value'].astype(int)
    fof_weights_df.columns = ['fund', 'value(IRMT)', 'weight(%)']
    fof_weights_df.reset_index(drop=True, inplace=True)
    fof_weights_df.index = fof_weights_df.index + 1
    fof_weights_df['weight(%)'] = fof_weights_df['weight(%)'].apply(lambda x: f"{x:,}")
    fof_weights_df['value(IRMT)'] = fof_weights_df['value(IRMT)'].apply(lambda x: f"{x:,}")
    
    # fof_color_mapping = {'Equity': '#FFB6C1', 'Fixed': '#87CEEB', 'Crypto': '#98FF98', 'USD': '#FFDAB9', 'Gold': '#E6E6FA', 'Safran': '#F08080'}
    # fof_colors = [fof_color_mapping.get(fund, '#d3d3d3') for fund in fof_weights_df['fund']]
    fof_weight_fig, ax = plt.subplots()
    ax.pie(fof_weights_df['weight(%)'], labels=fof_weights_df['fund'], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures pie is circular

    
    # end FOF


    # # VALUE SECTION
    # portfolio_funds_weight = PortfolioRisk.portfolio_fund_values(owner=owner, report_date=report_date)
    # portfolio_funds_weight['weight'] = round(portfolio_funds_weight['weight'] * 100, 1)
    # portfolio_total_value = portfolio_funds_weight['value'].sum()
    # portfolio_funds_weight['value'] = portfolio_funds_weight['value'] / 1e7
    # portfolio_funds_weight = portfolio_funds_weight.sort_values('value', ascending=False)
    # portfolio_funds_weight['value'] = portfolio_funds_weight['value'].astype(int)
    # portfolio_funds_weight.columns = ['fund', 'value(IRMT)', 'weight(%)']

    # # Fetch your portfolio
    # portfolio = HassibAPI.get_portfo_stock(owner=owner, date=report_date)
    # portfolio = portfolio[portfolio['fund'] == 'Equity_Quant']

    # # Calculate weights
    # portfolio['weight'] = portfolio['value'] / portfolio['value'].sum()

    # # Compute metrics
    # # from_date = '14030901'
    # # portfolio_std = float(PortfolioRisk.portfolio_std(portfolio=portfolio, from_date=from_date)) * 100
    # # portfolio_beta = float(PortfolioRisk.portfolio_beta(portfolio=portfolio, from_date=from_date))
    # # portfolio_VaR = PortfolioRisk.portfolio_VaR(portfolio=portfolio, confidential_level=.95, timehorizon='d')
    # # VaR_pct = portfolio_VaR['VaR'] * 100
    # # cVaR_pct = portfolio_VaR['cVaR'] * 100


    # # Fetch data
    # cc_portfolio_option = HassibAPI.get_portfo_option(owner=owner, date=report_date)
    # cc_portfolio_stock = HassibAPI.get_portfo_stock(owner=owner, date=report_date)
    # cc_portfolio_option = cc_portfolio_option[cc_portfolio_option['fund'].str.endswith('Fixed_CC')]
    # cc_portfolio_stock = cc_portfolio_stock[cc_portfolio_stock['fund'].str.endswith('Fixed_CC')]


    # # # CC underlyings_weight
    # # underlyings_weight = PortfolioRisk.portfolio_underlyings_weight(cc_portfolio_option, top_n=5).reset_index(drop=True)
    # # underlyings_weight.index = underlyings_weight.index + 1
    # # underlyings_weight['weight'] = (underlyings_weight['weight'] * 100).astype(int)
    # # underlyings_weight['strategy_value'] = underlyings_weight['strategy_value'] / 1e7
    # # underlyings_weight = underlyings_weight.sort_values('strategy_value', ascending=False)
    # # underlyings_weight['strategy_value'] = underlyings_weight['strategy_value'].astype(int)
    # # underlyings_weight.columns = ['fund', 'value(IRMT)', 'weight(%)']

    # # # CC contracts_weight
    # # contracts_weight = PortfolioRisk.portfolio_contracts_weight(cc_portfolio_option, top_n=5).reset_index(drop=True)
    # # contracts_weight.index = contracts_weight.index + 1
    # # contracts_weight.index = contracts_weight.index + 1
    # # contracts_weight['weight'] = (contracts_weight['weight'] * 100).astype(int)
    # # contracts_weight['strategy_value'] = contracts_weight['strategy_value'] / 1e7
    # # contracts_weight = contracts_weight.sort_values('strategy_value', ascending=False)
    # # contracts_weight['strategy_value'] = contracts_weight['strategy_value'].astype(int)
    # # contracts_weight.columns = ['fund', 'value(IRMT)', 'weight(%)']


    # # CC unbalancing
    # portfolio_cc_unbalance_df = PortfolioRisk.portfolio_cc_unbalance(cc_portfolio_option=cc_portfolio_option,cc_portfolio_stock=cc_portfolio_stock).reset_index(drop=True)
    # portfolio_cc_unbalance_df.index = portfolio_cc_unbalance_df.index + 1

    # # CC ttm and rcut
    # portfolio_cc_ttm = PortfolioRisk.portfolio_cc_ttm(cc_portfo=cc_portfolio_option)
    # portfolio_cc_rcut = PortfolioRisk.portfolio_cc_rcut(cc_portfo=cc_portfolio_option)

    # portfolio_cc_min_ttm = PortfolioRisk.portfolio_cc_min_ttm_list(cc_portfo=cc_portfolio_option, ttm_thershold=4).reset_index(drop=True)
    # portfolio_cc_min_ttm = portfolio_cc_min_ttm[['symbol', 'quantity', 'strategy_value', 'rcut', 'ttm']]
    # portfolio_cc_min_ttm['strategy_value'] = (portfolio_cc_min_ttm['strategy_value'] / 1e7).astype(int)
    # portfolio_cc_min_ttm['rcut'] = (portfolio_cc_min_ttm['rcut'] * 100).astype(int)
    # portfolio_cc_min_ttm.index = portfolio_cc_min_ttm.index + 1
    # portfolio_cc_min_ttm.columns = ['symbol', 'quantity', 'value (IRMT)', 'rcut', 'ttm']

    # portfolio_cc_min_rcut_list = PortfolioRisk.portfolio_cc_min_rcut_list(cc_portfo=cc_portfolio_option, rcut_thershold=-.06)
    # portfolio_cc_min_rcut_list.sort_values('rcut', inplace=True, ascending=False)
    # portfolio_cc_min_rcut_list.reset_index(drop=True, inplace=True)
    # portfolio_cc_min_rcut_list = portfolio_cc_min_rcut_list[['symbol', 'quantity', 'strategy_value', 'ttm', 'rcut']]
    # portfolio_cc_min_rcut_list['strategy_value'] = (portfolio_cc_min_rcut_list['strategy_value'] / 1e7).astype(int)
    # portfolio_cc_min_rcut_list['rcut'] = (portfolio_cc_min_rcut_list['rcut'] * 100).astype(int)
    # portfolio_cc_min_rcut_list.index = portfolio_cc_min_rcut_list.index + 1
    # portfolio_cc_min_rcut_list.columns = ['symbol', 'quantity', 'value (IRMT)', 'ttm', 'rcut (%)']


    # ************************************************************************************************************************************
    # --------------------------------------------------------------- STYLE -------------------------------------------------------
    # ************************************************************************************************************************************

    st.markdown("""
        <style>
                
            header {
                display: none !important   
            }
                
            html, body, [class*="css"] {
                font-size: 16px !important;  /* You can go lower like 12px or 10px */
            }

            h1, h2, h3, h4, h5, h6 {
                font-size: 1.5em !important;  /* Adjust heading sizes */
            }
                
            .stMainBlockContainer {
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                padding-top: 3rem !important;
                padding-bottom: 3rem !important;   
            }

            .stMarkdown {
                font-size: 12px !important;
            }

            .stButton>button, .stTextInput>div>input {
                font-size: 12px !important;
            }

            .stColumn {
                border-right: 1px solid #ccc;
                padding-right: 10px;
                padding-left: 10px;
            }
                
            .stColumn:last-child {
                border-right: none;
                padding-right: 0;
                # padding-left: 10px;
            }
                
            .stMetric label {
                display: block;
                text-align: center;
            }
                
            .stMetric {
                text-align: center;
            }
                
        </style>
    """, unsafe_allow_html=True)


    # ************************************************************************************************************************************
    # --------------------------------------------------------------- MAIN PAGE -------------------------------------------------------
    # ************************************************************************************************************************************

    col1, col2, col3 = st.columns([1.3, 1.3, 1])

    with col1:
        # st.markdown('<div class="vertical-line">', unsafe_allow_html=True)
        # st.header("⚙️ Assets")
        # st.write("---")

        # value_col1, value_col2, value_col3 = st.columns(3)
        # value_col1.metric("Value (IRMT)", f'{int(portfolio_total_value / 1e7):,}')
        # value_col2.metric("Cash (IRMT)", f'{int(portfolio_total_value / 1e7):,}')
        # value_col3.metric("Credit (IRMT)", f'{int(portfolio_total_value / 1e7):,}')

        st.write("---")

        st.subheader("FOF")
        st.dataframe(fof_weights_df)

        st.write("---")

        st.pyplot(fof_weight_fig)

        st.write("---")

        # asset_col1, asset_col2 = st.columns(2)
        # asset_col1.subheader("Underlyings Weight")
        # asset_col1.dataframe(underlyings_weight)
        # asset_col2.subheader("Contracts Weight")
        # asset_col2.dataframe(contracts_weight)

        # st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        pass
        # st.markdown('<div class="vertical-line">', unsafe_allow_html=True)
        # st.header("📊 Risk")
        # st.write("---")

        # equity_col1, equity_col2, equity_col3, equity_col4 = st.columns(4)
        # equity_col1.metric("Std (%)", f"{portfolio_std:.2f}")
        # equity_col2.metric("Beta", f"{portfolio_beta:.2f}")
        # # equity_col3.metric("VaR (%)", f"{VaR_pct:.2f}")
        # # equity_col4.metric("CVaR (%)", f"{cVaR_pct:.2f}")

        # st.write("---")

        # risk_col1, risk_col2, risk_col3= st.columns([2, 1, 1])
        # risk_col1.subheader("CC Unbalance")
        # risk_col1.dataframe(portfolio_cc_unbalance_df)
        # risk_col2.metric("portfolio ttm", int(portfolio_cc_ttm))
        # risk_col3.metric("portfolio rcut (%)", round(portfolio_cc_rcut * 100, 1))

        # st.write("---")

        # st.subheader("CC Close Maturity")
        # st.dataframe(portfolio_cc_min_ttm)   

        # st.write("---")

        # st.subheader("CC High-Risk")
        # st.dataframe(portfolio_cc_min_rcut_list)

        # st.markdown('</div>', unsafe_allow_html=True)

    # Third column with no border
    with col3:
        pass
        # st.markdown('<div class="right_container1">', unsafe_allow_html=True)
        # st.header("📊 Return")

        # st.subheader("Funds Weight")
        # portfolio_funds_weight.reset_index(drop=True, inplace=True)
        # portfolio_funds_weight.index = portfolio_funds_weight.index + 1
        # # portfolio_funds_weight['value(IRMT)'] = portfolio_funds_weight['value(IRMT)'].apply(lambda x: f"{x:,}")
        # st.dataframe(portfolio_funds_weight)

        # st.write("---")

        # fig, ax = plt.subplots()
        # ax.pie(portfolio_funds_weight['weight(%)'], labels=portfolio_funds_weight['fund'], autopct='%1.1f%%', startangle=90)
        # ax.axis('equal')  # Equal aspect ratio ensures pie is circular
        # # Show in Streamlit
        # st.pyplot(fig)

        # st.markdown('</div>', unsafe_allow_html=True)

