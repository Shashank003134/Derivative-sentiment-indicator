import streamlit as st
from jugaad_data.nse import NSELive
import pandas as pd
import plotly.graph_objects as go
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

tab1, tab2, tab3, tab4 = st.tabs(['Nifty', 'BankNifty', 'FinNifty', 'MidcapNifty'])
with tab1:
    show_dashboard('NIFTY')
with tab2:
    show_dashboard('BANKNIFTY')
with tab3:
    show_dashboard('FINNIFTY')
with tab4:
    show_dashboard('MIDCPNIFTY')

st.divider()
st.markdown('<h4 style="text-align:center; color:gray;">Data Source: NSE India | Auto-refreshes every 5 minutes | Built by Shashank Agarwal</h4>', unsafe_allow_html=True)
