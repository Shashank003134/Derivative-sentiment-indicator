import time
import streamlit as st
import yfinance as yf
import streamlit.components.v1 as components
from jugaad_data.nse import NSELive
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title='OptionsPulse', page_icon='📊', layout='wide')
st.markdown('<h1 style="text-align:center; color:#1f77b4;">OptionsPulse</h1>', unsafe_allow_html=True)
st.markdown('<h4 style="text-align:center; color:#444444;"><i>Decode the Market. Dominate the Trade.</i></h4>', unsafe_allow_html=True)
st.markdown('<h5 style="text-align:center; color:gray;">Live F&O Data Analysis - PCR | Max Pain | OI | Global Markets | Trade Analyser</h5>', unsafe_allow_html=True)

col_refresh, col_time, col_timer, col_dark = st.columns([1, 2, 2, 1])
with col_refresh:
    if st.button('Refresh Data'):
        st.cache_data.clear()
        st.rerun()
with col_time:
    st.markdown(f'<p style="color:gray;">Last Updated: {datetime.now().strftime("%d %b %Y %I:%M %p")}</p>', unsafe_allow_html=True)
with col_timer:
    st.markdown('<p style="color:gray;">Auto refreshes every 1 minute</p>', unsafe_allow_html=True)
with col_dark:
    dark_mode = st.toggle('Dark Mode')
if dark_mode:
    st.markdown('''
    <style>
    .stApp { background-color: #1e1e1e; color: white; }
    .stMetric { background-color: #2d2d2d; color: white; border-radius: 8px; padding: 10px; }
    .stMetric label { color: #aaaaaa !important; }
    .stMetric div { color: white !important; }
    .stDataFrame { background-color: #2d2d2d; color: white; }
    .stSelectbox label { color: white !important; }
    .stSelectbox div { background-color: #2d2d2d; color: white; }
    .stTextInput label { color: white !important; }
    .stTextInput div { background-color: #2d2d2d; color: white; }
    .stButton button { background-color: #1f77b4; color: white; }
    .stTabs div { color: white; }
    .stMarkdown { color: white; }
    div[data-testid='stMetricValue'] { color: white !important; }
    div[data-testid='stMetricLabel'] { color: #aaaaaa !important; }
    .stFileUploader { background-color: #2d2d2d; color: white; }
    .stDivider { border-color: #444444; }
    </style>
    ''', unsafe_allow_html=True)
st.divider()

@st.cache_data(ttl=60)
def fetch_data(index_name):
    try:
        n = NSELive()
        q2 = n.index_option_chain(index_name)
        if 'records' not in q2:
            return None, None, None, None
        nifty_spot = q2['records']['underlyingValue']
        data = q2['records']['data']
        ce_data = []
        pe_data = []
        for item in data:
            if 'CE' in item:
                ce_data.append({'strike': item['strikePrice'], 'expiry': item['CE']['expiryDate'], 'ce_oi': item['CE']['openInterest'], 'ce_volume': item['CE']['totalTradedVolume'], 'ce_iv': item['CE']['impliedVolatility']})
            if 'PE' in item:
                pe_data.append({'strike': item['strikePrice'], 'expiry': item['PE']['expiryDate'], 'pe_oi': item['PE']['openInterest'], 'pe_volume': item['PE']['totalTradedVolume'], 'pe_iv': item['PE']['impliedVolatility']})
        ce_df = pd.DataFrame(ce_data)
        pe_df = pd.DataFrame(pe_data)
        merged_df = pd.merge(ce_df, pe_df, on=['strike', 'expiry'])
        merged_df['total_oi'] = merged_df['ce_oi'] + merged_df['pe_oi']
        return nifty_spot, ce_df, pe_df, merged_df
    except Exception as e:
        return None, None, None, None

def make_gauge(title, value, min_val, max_val, color):
    fig = go.Figure(go.Indicator(
        mode='gauge+number',
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': color},
            'steps': [
                {'range': [min_val, (max_val+min_val)/2], 'color': '#ffcccc'},
                {'range': [(max_val+min_val)/2, max_val], 'color': '#ccffcc'}
            ],
            'threshold': {'line': {'color': 'black', 'width': 4}, 'thickness': 0.75, 'value': value}
        }
    ))
    fig.update_layout(height=250, margin=dict(t=40, b=0, l=20, r=20))
    return fig

def show_dashboard(index_name):
    with st.spinner('Fetching live NSE data...'):
        nifty_spot, ce_df, pe_df, merged_df = fetch_data(index_name)
    if nifty_spot is None:
        st.warning('NSE data not available right now. Market may be closed or NSE is busy. Please try again in a few minutes.')
        return
    total_ce_oi = ce_df['ce_oi'].sum()
    total_pe_oi = pe_df['pe_oi'].sum()
    pcr = total_pe_oi / total_ce_oi
    max_pain_strike = merged_df.loc[merged_df['total_oi'].idxmax(), 'strike']
    atm_df = merged_df[(merged_df['strike'] >= nifty_spot - 1000) & (merged_df['strike'] <= nifty_spot + 1000)].copy()
    above_spot = atm_df[atm_df['strike'] > nifty_spot]
    below_spot = atm_df[atm_df['strike'] < nifty_spot]
    max_ce_oi_strike = above_spot.loc[above_spot['ce_oi'].idxmax(), 'strike'] if len(above_spot) > 0 else atm_df.loc[atm_df['ce_oi'].idxmax(), 'strike']
    max_pe_oi_strike = below_spot.loc[below_spot['pe_oi'].idxmax(), 'strike'] if len(below_spot) > 0 else atm_df.loc[atm_df['pe_oi'].idxmax(), 'strike']
    if pcr > 1.2:
        pcr_score = 2
        pcr_signal = 'BULLISH'
        pcr_color = 'green'
    elif pcr < 0.8:
        pcr_score = -2
        pcr_signal = 'BEARISH'
        pcr_color = 'red'
    else:
        pcr_score = 0
        pcr_signal = 'NEUTRAL'
        pcr_color = 'orange'
    if nifty_spot < max_pain_strike:
        mp_score = 1
        mp_signal = 'BULLISH'
        mp_color = 'green'
    elif nifty_spot > max_pain_strike:
        mp_score = -1
        mp_signal = 'BEARISH'
        mp_color = 'red'
    else:
        mp_score = 0
        mp_signal = 'NEUTRAL'
        mp_color = 'orange'
    if nifty_spot > max_ce_oi_strike:
        oi_score = 2
        oi_result = 'BULLISH BREAKOUT'
        oi_color = 'green'
    elif nifty_spot < max_pe_oi_strike:
        oi_score = -2
        oi_result = 'BEARISH BREAKDOWN'
        oi_color = 'red'
    else:
        oi_score = 0
        oi_result = 'RANGE BOUND'
        oi_color = 'orange'
    total_score = pcr_score + mp_score + oi_score
    if total_score >= 3:
        overall = 'STRONGLY BULLISH'
        overall_color = '#00aa00'
    elif total_score > 0:
        overall = 'MILDLY BULLISH'
        overall_color = '#55cc55'
    elif total_score == 0:
        overall = 'NEUTRAL'
        overall_color = 'orange'
    elif total_score > -3:
        overall = 'MILDLY BEARISH'
        overall_color = '#cc5555'
    else:
        overall = 'STRONGLY BEARISH'
        overall_color = '#aa0000'
    st.markdown(f'<h2 style="text-align:center;">{index_name} Spot: <span style="color:#1f77b4;">{nifty_spot}</span></h2>', unsafe_allow_html=True)
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<h4 style="text-align:center;">PCR</h4>', unsafe_allow_html=True)
        st.markdown(f'<h2 style="text-align:center;">{round(pcr,2)}</h2>', unsafe_allow_html=True)
        st.markdown(f'<h3 style="text-align:center; color:{pcr_color};">{pcr_signal}</h3>', unsafe_allow_html=True)
    with col2:
        st.markdown('<h4 style="text-align:center;">Max Pain</h4>', unsafe_allow_html=True)
        st.markdown(f'<h2 style="text-align:center;">{max_pain_strike}</h2>', unsafe_allow_html=True)
        st.markdown(f'<h3 style="text-align:center; color:{mp_color};">{mp_signal}</h3>', unsafe_allow_html=True)
    with col3:
        st.markdown('<h4 style="text-align:center;">OI Analysis</h4>', unsafe_allow_html=True)
        st.markdown(f'<h2 style="text-align:center;">-</h2>', unsafe_allow_html=True)
        st.markdown(f'<h3 style="text-align:center; color:{oi_color};">{oi_result}</h3>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<h3 style="text-align:center;">Gauge Charts</h3>', unsafe_allow_html=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(make_gauge('PCR', round(pcr,2), 0, 2, pcr_color), use_container_width=True, key=f'pcr_{index_name}')
    with g2:
        mp_diff = round(max_pain_strike - nifty_spot, 0)
        st.plotly_chart(make_gauge('Max Pain Diff', mp_diff, -1000, 1000, mp_color), use_container_width=True, key=f'mp_{index_name}')
    with g3:
        st.plotly_chart(make_gauge('Sentiment Score', total_score, -5, 5, overall_color), use_container_width=True, key=f'score_{index_name}')
    st.divider()
    st.markdown(f'<h2 style="text-align:center;">Market Mood: <span style="color:{overall_color};">{overall}</span></h2>', unsafe_allow_html=True)
    st.markdown(f'<h3 style="text-align:center;">Score: {total_score} / 5</h3>', unsafe_allow_html=True)
    st.divider()
    st.subheader('OI Chart - Support & Resistance')
    fig = go.Figure()
    fig.add_trace(go.Bar(x=atm_df['strike'], y=atm_df['ce_oi'], name='Call OI', marker_color='red'))
    fig.add_trace(go.Bar(x=atm_df['strike'], y=atm_df['pe_oi'], name='Put OI', marker_color='green'))
    fig.add_vline(x=nifty_spot, line_dash='dash', line_color='blue', annotation_text='Spot')
    fig.update_layout(title='Call vs Put OI Near ATM', xaxis_title='Strike Price', yaxis_title='Open Interest', barmode='group')
    st.plotly_chart(fig, use_container_width=True, key=f'oi_{index_name}')
    st.divider()
    st.subheader('Key Levels')
    lev1, lev2, lev3, lev4 = st.columns(4)
    with lev1:
        st.metric('Spot Price', nifty_spot)
    with lev2:
        st.metric('Max Pain', max_pain_strike)
    with lev3:
        st.metric('Resistance (Max CE OI)', max_ce_oi_strike)
    with lev4:
        st.metric('Support (Max PE OI)', max_pe_oi_strike)

def show_strategy():
    st.markdown('<h2 style="text-align:center; color:#1f77b4;">Strategy Analyser - Nine Star Broking</h2>', unsafe_allow_html=True)
    st.markdown('<h5 style="text-align:center; color:gray;">Real Trade Data Analysis - Short Straddle Performance</h5>', unsafe_allow_html=True)
    st.divider()
    df = pd.read_excel('Trades.xlsx', sheet_name='All trades')
    weekly_pnl = df.groupby('Week')['Net Value'].sum().reset_index()
    weekly_pnl.columns = ['Week', 'Net PnL']
    total_weeks = len(weekly_pnl)
    profit_weeks = len(weekly_pnl[weekly_pnl['Net PnL'] > 0])
    loss_weeks = len(weekly_pnl[weekly_pnl['Net PnL'] < 0])
    win_rate = round((profit_weeks / total_weeks) * 100, 2)
    total_pnl = round(weekly_pnl['Net PnL'].sum(), 2)
    best_week = weekly_pnl.loc[weekly_pnl['Net PnL'].idxmax()]
    worst_week = weekly_pnl.loc[weekly_pnl['Net PnL'].idxmin()]
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric('Total Weeks', total_weeks)
    with m2:
        st.metric('Win Rate', str(win_rate) + '%')
    with m3:
        st.metric('Total Net P&L', 'Rs ' + str(round(total_pnl/100000, 2)) + 'L')
    with m4:
        st.metric('Profit Weeks', str(profit_weeks) + ' / ' + str(total_weeks))
    st.divider()
    weekly_pnl['Color'] = weekly_pnl['Net PnL'].apply(lambda x: 'green' if x > 0 else 'red')
    fig1 = go.Figure(go.Bar(x=weekly_pnl['Week'], y=weekly_pnl['Net PnL'], marker_color=weekly_pnl['Color']))
    fig1.update_layout(title='Weekly P&L', xaxis_title='Week', yaxis_title='Net P&L (Rs)')
    st.plotly_chart(fig1, use_container_width=True, key='weekly_pnl')
    st.divider()
    index_pnl = df.groupby('Symbol/ScripId')['Net Value'].sum().reset_index()
    index_pnl.columns = ['Index', 'Net PnL']
    index_pnl['Color'] = index_pnl['Net PnL'].apply(lambda x: 'green' if x > 0 else 'red')
    col_a, col_b = st.columns(2)
    with col_a:
        fig2 = go.Figure(go.Bar(x=index_pnl['Index'], y=index_pnl['Net PnL'], marker_color=index_pnl['Color']))
        fig2.update_layout(title='Index Wise P&L', xaxis_title='Index', yaxis_title='Net P&L (Rs)')
        st.plotly_chart(fig2, use_container_width=True, key='index_pnl')
    with col_b:
        trade_pnl = df.groupby('Trade Type')['Net Value'].sum().reset_index()
        trade_pnl.columns = ['Trade Type', 'Net PnL']
        trade_pnl = trade_pnl.dropna()
        trade_pnl['Color'] = trade_pnl['Net PnL'].apply(lambda x: 'green' if x > 0 else 'red')
        fig3 = go.Figure(go.Bar(x=trade_pnl['Trade Type'], y=trade_pnl['Net PnL'], marker_color=trade_pnl['Color']))
        fig3.update_layout(title='Trade Type P&L', xaxis_title='Trade Type', yaxis_title='Net P&L (Rs)')
        st.plotly_chart(fig3, use_container_width=True, key='trade_pnl')
    st.divider()
    df['Month'] = pd.to_datetime(df['Date']).dt.strftime('%b %Y')
    monthly_pnl = df.groupby('Month')['Net Value'].sum().reset_index()
    monthly_pnl.columns = ['Month', 'Net PnL']
    monthly_pnl['Color'] = monthly_pnl['Net PnL'].apply(lambda x: 'green' if x > 0 else 'red')
    fig4 = go.Figure(go.Bar(x=monthly_pnl['Month'], y=monthly_pnl['Net PnL'], marker_color=monthly_pnl['Color']))
    fig4.update_layout(title='Monthly P&L', xaxis_title='Month', yaxis_title='Net P&L (Rs)')
    st.plotly_chart(fig4, use_container_width=True, key='monthly_pnl')
    st.divider()
    st.subheader('Best & Worst Weeks')
    bw1, bw2 = st.columns(2)
    with bw1:
        st.success('Best Week: ' + str(best_week['Week']) + ' -> Rs ' + str(round(best_week['Net PnL'], 2)))
    with bw2:
        st.error('Worst Week: ' + str(worst_week['Week']) + ' -> Rs ' + str(round(worst_week['Net PnL'], 2)))

def show_analyser():
    st.markdown('<h2 style="text-align:center; color:#1f77b4;">Trade Analyser</h2>', unsafe_allow_html=True)
    st.markdown('<h5 style="text-align:center; color:gray;">Upload your trade data and get instant performance analytics</h5>', unsafe_allow_html=True)
    st.divider()
    uploaded_file = st.file_uploader('Upload your Trade Excel File', type=['xlsx', 'xls', 'csv'])
    if uploaded_file is not None:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            sheet_names = pd.ExcelFile(uploaded_file).sheet_names
            selected_sheet = st.selectbox('Select Sheet', sheet_names)
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        st.success('File uploaded! ' + str(len(df)) + ' rows found.')
        st.divider()
        st.subheader('Step 1 - Map Your Columns')
        all_cols = ['-- Select --'] + list(df.columns)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            date_col = st.selectbox('Date Column', all_cols)
        with c2:
            pnl_col = st.selectbox('P&L / Net Value Column', all_cols)
        with c3:
            index_col = st.selectbox('Index / Symbol Column', all_cols)
        with c4:
            strategy_col = st.selectbox('Strategy / Trade Type Column', all_cols)
        st.divider()
        chart_type = st.selectbox('Select Chart Type', ['Bar Chart', 'Line Chart', 'Area Chart', 'Pie Chart'], key='chart_selector')
        st.divider()
        st.divider()
        st.subheader('Step 3 - Filter by Date Range (Optional)')
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input('Start Date', value=pd.to_datetime('2025-01-01'))
        with date_col2:
            end_date = st.date_input('End Date', value=pd.to_datetime('today'))
        st.divider()
        if st.button('Analyse My Trades'):
            if '-- Select --' in [date_col, pnl_col, index_col, strategy_col]:
                st.error('Please map all 4 columns before analysing!')
            else:
                df = df.rename(columns={date_col: 'Date', pnl_col: 'Net PnL', index_col: 'Index', strategy_col: 'Strategy'})
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Net PnL'] = pd.to_numeric(df['Net PnL'], errors='coerce')
                df = df.dropna(subset=['Date', 'Net PnL'])
                df = df[(df['Date'] >= pd.to_datetime(start_date)) & (df['Date'] <= pd.to_datetime(end_date))]
                df['Month'] = df['Date'].dt.strftime('%b %Y')
                total_pnl = round(df['Net PnL'].sum(), 2)
                total_trades = len(df)
                profit_trades = len(df[df['Net PnL'] > 0])
                loss_trades = len(df[df['Net PnL'] < 0])
                win_rate = round((profit_trades / total_trades) * 100, 2)
                avg_profit = round(df[df['Net PnL'] > 0]['Net PnL'].mean(), 2)
                avg_loss = round(df[df['Net PnL'] < 0]['Net PnL'].mean(), 2)
                st.markdown('<h3 style="text-align:center;">Overall Performance</h3>', unsafe_allow_html=True)
                r1, r2, r3, r4, r5, r6 = st.columns(6)
                with r1:
                    st.metric('Total Trades', total_trades)
                with r2:
                    st.metric('Win Rate', str(win_rate) + '%')
                with r3:
                    st.metric('Total P&L', 'Rs ' + str(round(total_pnl/100000, 2)) + 'L')
                with r4:
                    st.metric('Profit Trades', profit_trades)
                with r5:
                    st.metric('Avg Profit', 'Rs ' + str(avg_profit))
                with r6:
                    st.metric('Avg Loss', 'Rs ' + str(avg_loss))
                st.divider()
                st.markdown('<h3 style="text-align:center;">Risk Metrics</h3>', unsafe_allow_html=True)
                import numpy as np
                daily_pnl = df.groupby('Date')['Net PnL'].sum()
                sharpe_ratio = round((daily_pnl.mean() / daily_pnl.std()) * (252 ** 0.5), 2)
                max_drawdown = round(((daily_pnl.cumsum() - daily_pnl.cumsum().cummax()) / daily_pnl.cumsum().cummax().abs()).min() * 100, 2)
                profit_factor = round(df[df['Net PnL'] > 0]['Net PnL'].sum() / abs(df[df['Net PnL'] < 0]['Net PnL'].sum()), 2)
                max_profit = round(df['Net PnL'].max(), 2)
                max_loss = round(df['Net PnL'].min(), 2)
                rk1, rk2, rk3, rk4, rk5 = st.columns(5)
                with rk1:
                    st.metric('Sharpe Ratio', sharpe_ratio)
                with rk2:
                    st.metric('Max Drawdown', str(max_drawdown) + '%')
                with rk3:
                    st.metric('Profit Factor', profit_factor)
                with rk4:
                    st.metric('Max Single Profit', 'Rs ' + str(max_profit))
                with rk5:
                    st.metric('Max Single Loss', 'Rs ' + str(max_loss))
                st.divider()
                st.subheader('Strategy Wise Performance')
                strategy_pnl = df.groupby('Strategy')['Net PnL'].agg(['sum', 'count', lambda x: (x > 0).sum()]).reset_index()
                strategy_pnl.columns = ['Strategy', 'Total PnL', 'Total Trades', 'Profit Trades']
                strategy_pnl['Win Rate'] = (strategy_pnl['Profit Trades'] / strategy_pnl['Total Trades'] * 100).round(2)
                strategy_pnl['Total PnL'] = strategy_pnl['Total PnL'].round(2)
                strategy_pnl['Color'] = strategy_pnl['Total PnL'].apply(lambda x: 'green' if x > 0 else 'red')
                if chart_type == 'Bar Chart':
                    fig_s = go.Figure(go.Bar(x=strategy_pnl['Strategy'], y=strategy_pnl['Total PnL'], marker_color=strategy_pnl['Color']))
                elif chart_type == 'Line Chart':
                    fig_s = go.Figure(go.Scatter(x=strategy_pnl['Strategy'], y=strategy_pnl['Total PnL'], mode='lines+markers', line=dict(color='blue', width=2)))
                elif chart_type == 'Area Chart':
                    fig_s = go.Figure(go.Scatter(x=strategy_pnl['Strategy'], y=strategy_pnl['Total PnL'], fill='tozeroy', mode='lines', line=dict(color='blue')))
                else:
                    fig_s = go.Figure(go.Pie(labels=strategy_pnl['Strategy'], values=strategy_pnl['Total PnL'].abs()))
                fig_s.update_layout(title='Strategy Wise P&L')
                st.plotly_chart(fig_s, use_container_width=True, key='strategy_pnl')
                st.dataframe(strategy_pnl[['Strategy', 'Total PnL', 'Total Trades', 'Win Rate']].sort_values('Total PnL', ascending=False), use_container_width=True)
                st.divider()
                st.subheader('Index Wise Performance')
                index_pnl = df.groupby('Index')['Net PnL'].sum().reset_index()
                index_pnl.columns = ['Index', 'Total PnL']
                index_pnl['Color'] = index_pnl['Total PnL'].apply(lambda x: 'green' if x > 0 else 'red')
                if chart_type == 'Bar Chart':
                    fig_i = go.Figure(go.Bar(x=index_pnl['Index'], y=index_pnl['Total PnL'], marker_color=index_pnl['Color']))
                elif chart_type == 'Line Chart':
                    fig_i = go.Figure(go.Scatter(x=index_pnl['Index'], y=index_pnl['Total PnL'], mode='lines+markers', line=dict(color='blue', width=2)))
                elif chart_type == 'Area Chart':
                    fig_i = go.Figure(go.Scatter(x=index_pnl['Index'], y=index_pnl['Total PnL'], fill='tozeroy', mode='lines', line=dict(color='blue')))
                else:
                    fig_i = go.Figure(go.Pie(labels=index_pnl['Index'], values=index_pnl['Total PnL'].abs()))
                fig_i.update_layout(title='Index Wise P&L')
                st.plotly_chart(fig_i, use_container_width=True, key='index_pnl_analyser')
                st.divider()
                st.subheader('Monthly Performance')
                monthly_pnl = df.groupby('Month')['Net PnL'].sum().reset_index()
                monthly_pnl['Color'] = monthly_pnl['Net PnL'].apply(lambda x: 'green' if x > 0 else 'red')
                if chart_type == 'Bar Chart':
                    fig_m = go.Figure(go.Bar(x=monthly_pnl['Month'], y=monthly_pnl['Net PnL'], marker_color=monthly_pnl['Color']))
                elif chart_type == 'Line Chart':
                    fig_m = go.Figure(go.Scatter(x=monthly_pnl['Month'], y=monthly_pnl['Net PnL'], mode='lines+markers', line=dict(color='blue', width=2)))
                elif chart_type == 'Area Chart':
                    fig_m = go.Figure(go.Scatter(x=monthly_pnl['Month'], y=monthly_pnl['Net PnL'], fill='tozeroy', mode='lines', line=dict(color='blue')))
                else:
                    fig_m = go.Figure(go.Pie(labels=monthly_pnl['Month'], values=monthly_pnl['Net PnL'].abs()))
                fig_m.update_layout(title='Monthly P&L')
                st.plotly_chart(fig_m, use_container_width=True, key='monthly_pnl_analyser')
                st.divider()
                st.subheader('Cumulative P&L Curve')
                df_sorted = df.sort_values('Date')
                df_sorted['Cumulative PnL'] = df_sorted['Net PnL'].cumsum()
                fig_c = go.Figure(go.Scatter(x=df_sorted['Date'], y=df_sorted['Cumulative PnL'], mode='lines', line=dict(color='blue', width=2)))
                fig_c.update_layout(title='Cumulative P&L Over Time', xaxis_title='Date', yaxis_title='Cumulative P&L (Rs)')
                st.plotly_chart(fig_c, use_container_width=True, key='cumulative_pnl')

@st.cache_data(ttl=300)
def get_price(ticker):
    try:
        return round(yf.Ticker(ticker).fast_info['last_price'], 2)
    except:
        return 'N/A'

def show_global_markets():
    st.markdown('<h2 style="text-align:center; color:#1f77b4;">Global Market Watch</h2>', unsafe_allow_html=True)
    st.markdown('<h5 style="text-align:center; color:gray;">Live prices — Indices | Commodities | Currencies | Updates every 5 minutes</h5>', unsafe_allow_html=True)
    st.divider()
    st.subheader('Global Indices')
    g1, g2, g3, g4, g5, g6 = st.columns(6)
    with g1:
        st.metric('S&P 500', get_price('^GSPC'))
    with g2:
        st.metric('Dow Jones', get_price('^DJI'))
    with g3:
        st.metric('Nasdaq', get_price('^IXIC'))
    with g4:
        st.metric('FTSE 100', get_price('^FTSE'))
    with g5:
        st.metric('Nikkei', get_price('^N225'))
    with g6:
        st.metric('Hang Seng', get_price('^HSI'))
    st.divider()
    st.subheader('Commodities')
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric('Gold (USD/oz)', get_price('GC=F'))
    with c2:
        st.metric('Silver (USD/oz)', get_price('SI=F'))
    with c3:
        st.metric('Crude Oil (USD/bbl)', get_price('CL=F'))
    with c4:
        st.metric('Natural Gas', get_price('NG=F'))
    st.divider()
    st.subheader('Currencies')
    cur1, cur2, cur3, cur4, cur5, cur6 = st.columns(6)
    with cur1:
        st.metric('USD/INR', get_price('USDINR=X'))
    with cur2:
        st.metric('EUR/INR', get_price('EURINR=X'))
    with cur3:
        st.metric('GBP/INR', get_price('GBPINR=X'))
    with cur4:
        st.metric('EUR/USD', get_price('EURUSD=X'))
    with cur5:
        st.metric('GBP/USD', get_price('GBPUSD=X'))
    with cur6:
        st.metric('USD/JPY', get_price('USDJPY=X'))
    st.divider()
    st.subheader('Indian Markets')
    i1, i2, i3 = st.columns(3)
    with i1:
        st.metric('Nifty 50', get_price('^NSEI'))
    with i2:
        st.metric('Sensex', get_price('^BSESN'))
    with i3:
        st.metric('Bank Nifty', get_price('^NSEBANK'))
    st.divider()
    st.markdown('<h4 style="text-align:center; color:gray;">Data Source: Yahoo Finance | Prices may be delayed by 15 minutes</h4>', unsafe_allow_html=True)
    st.divider()
    st.subheader('TradingView Charts')
    chart_col1, chart_col2, chart_col3 = st.columns(3)
    with chart_col1:
        common_symbols = {
            'Custom (type below)': '',
            '--- Commodities ---': '',
            'Gold': 'TVC:GOLD',
            'Silver': 'TVC:SILVER',
            'Crude Oil': 'TVC:USOIL',
            '--- Currencies ---': '',
            'USD/INR': 'FX:USDINR',
            'EUR/USD': 'FX:EURUSD',
            'GBP/USD': 'FX:GBPUSD',
            'USD/JPY': 'FX:USDJPY',
            '--- Global Indices ---': '',
            'S&P 500': 'FOREXCOM:SPXUSD',
            'Nasdaq': 'FOREXCOM:NSXUSD',
            'Dow Jones': 'FOREXCOM:DJI',
            'FTSE 100': 'FOREXCOM:FTSUSD',
            'DAX': 'INDEX:DAX',
            'Nikkei': 'INDEX:NI225',
            'Hang Seng': 'INDEX:HSI',
            '--- US Stocks ---': '',
            'Apple': 'NASDAQ:AAPL',
            'Google': 'NASDAQ:GOOGL',
            'Tesla': 'NASDAQ:TSLA',
            'Microsoft': 'NASDAQ:MSFT',
        }
        selected_name = st.selectbox('Select Common Symbol', list(common_symbols.keys()), key='tv_dropdown')
        custom_symbol = st.text_input('Or Type Custom TradingView Symbol', value='TVC:GOLD', key='tv_symbol', help='Examples: TVC:GOLD, BSE:SENSEX, NSE:RELIANCE')
        if selected_name != 'Custom (type below)' and not selected_name.startswith('---'):
            chart_symbol = common_symbols[selected_name]
        else:
            chart_symbol = custom_symbol
    with chart_col2:
        chart_interval = st.selectbox('Interval', ['1', '5', '15', '30', '60', 'D', 'W'], key='tv_interval')
    with chart_col3:
        chart_theme = st.selectbox('Theme', ['light', 'dark'], key='tv_theme')
    tradingview_widget = f"""
    <iframe src='https://s.tradingview.com/widgetembed/?frameElementId=tradingview&symbol={chart_symbol}&interval={chart_interval}&hidesidetoolbar=0&symboledit=1&saveimage=1&toolbarbg=f1f3f6&studies=[]&theme={chart_theme}&style=1&timezone=Asia%2FKolkata&withdateranges=1&showpopupbutton=1&studies_overrides={{}}&overrides={{}}&enabled_features=[]&disabled_features=[]&locale=en'
    width='100%' height='500' frameborder='0' allowtransparency='true' scrolling='no'></iframe>
    """
    st.components.v1.html(tradingview_widget, height=520)

def show_feedback():
    st.markdown('<h2 style="text-align:center; color:#1f77b4;">Feedback</h2>', unsafe_allow_html=True)
    st.markdown('<h5 style="text-align:center; color:gray;">Help us improve OptionsPulse!</h5>', unsafe_allow_html=True)
    st.divider()
    feedback_widget = '<iframe src="https://docs.google.com/forms/d/e/1FAIpQLScixODBP9qA2xUdy2JpVtyRp9T3tLOAoOodgwEOIyrlSfqyug/viewform?embedded=true" width="100%" height="1608" frameborder="0" marginheight="0" marginwidth="0">Loading...</iframe>'
    st.components.v1.html(feedback_widget, height=1628)

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(['Nifty', 'BankNifty', 'FinNifty', 'MidcapNifty', 'Trade Analyser', 'Global Markets', 'Feedback'])
with tab1:
    show_dashboard('NIFTY')
with tab2:
    show_dashboard('BANKNIFTY')
with tab3:
    show_dashboard('FINNIFTY')
with tab4:
    show_dashboard('MIDCPNIFTY')
with tab5:
    show_analyser()
with tab6:
    show_global_markets()
with tab7:
    show_feedback()

st.divider()
st.markdown('<h4 style="text-align:center; color:gray;">© 2026 OptionsPulse | Built by Shashank Agarwal | Data: NSE India & Yahoo Finance | All Rights Reserved</h4>', unsafe_allow_html=True)
