import streamlit as st
from jugaad_data.nse import NSELive
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title='Derivative Sentiment Indicator', layout='wide')
st.markdown('<h1 style="text-align:center; color:#1f77b4;">Derivative Sentiment Indicator</h1>', unsafe_allow_html=True)
st.markdown('<h4 style="text-align:center; color:gray;">Live F&O Data Analysis - PCR | Max Pain | OI</h4>', unsafe_allow_html=True)

col_refresh, col_time = st.columns([1, 3])
with col_refresh:
    if st.button('Refresh Data'):
        st.cache_data.clear()
with col_time:
    st.markdown(f'<p style="color:gray;">Last Updated: {datetime.now().strftime("%d %b %Y %I:%M %p")}</p>', unsafe_allow_html=True)
st.divider()

@st.cache_data(ttl=300)
def fetch_data(index_name):
    n = NSELive()
    q2 = n.index_option_chain(index_name)
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
    total_ce_oi = ce_df['ce_oi'].sum()
    total_pe_oi = pe_df['pe_oi'].sum()
    pcr = total_pe_oi / total_ce_oi
    max_pain_strike = merged_df.loc[merged_df['total_oi'].idxmax(), 'strike']
    atm_df = merged_df[(merged_df['strike'] >= nifty_spot - 1000) & (merged_df['strike'] <= nifty_spot + 1000)].copy()
    max_ce_oi_strike = atm_df.loc[atm_df['ce_oi'].idxmax(), 'strike']
    max_pe_oi_strike = atm_df.loc[atm_df['pe_oi'].idxmax(), 'strike']
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
        if st.button('Analyse My Trades'):
            if '-- Select --' in [date_col, pnl_col, index_col, strategy_col]:
                st.error('Please map all 4 columns before analysing!')
            else:
                df = df.rename(columns={date_col: 'Date', pnl_col: 'Net PnL', index_col: 'Index', strategy_col: 'Strategy'})
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df['Net PnL'] = pd.to_numeric(df['Net PnL'], errors='coerce')
                df = df.dropna(subset=['Date', 'Net PnL'])
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

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Nifty', 'BankNifty', 'FinNifty', 'MidcapNifty', 'Trade Analyser'])
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

st.divider()
st.markdown('<h4 style="text-align:center; color:gray;">Data Source: NSE India | Built by Shashank Agarwal</h4>', unsafe_allow_html=True)
