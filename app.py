%%writefile app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Forex Screener", layout="wide")
st.title("🤖 AI-Powered Forex Screener")

# --- SIDEBAR INTERFACE ---
st.sidebar.header("⚙️ Filter Settings")
rsi_oversold = st.sidebar.slider("Buy Threshold (RSI Oversold)", 10, 50, 40)
rsi_overbought = st.sidebar.slider("Sell Threshold (RSI Overbought)", 50, 90, 60)

st.sidebar.markdown("---")
st.sidebar.header("🔧 Debug Tools")
# NEW: An override switch!
strict_mode = st.sidebar.checkbox("Strict Mode (Require MACD & AI)", value=True)

# --- DATA PIPELINE ---
@st.cache_data(ttl=3600) 
def fetch_data():
    major_pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD']
    data_dict = {}
    for pair in major_pairs:
        ticker = f"{pair.replace('/', '')}=X"
        df = yf.Ticker(ticker).history(period="3mo", interval="1d")
        if not df.empty:
            data_dict[pair] = df[['Close']]
    return data_dict

market_data = fetch_data()

ai_sentiment_data = {
    'EUR/USD': 'BEARISH', 
    'GBP/USD': 'NEUTRAL', 
    'USD/JPY': 'BULLISH', 
    'AUD/USD': 'BULLISH'  
}

# --- LOGIC ENGINE ---
actionable_trades = []
all_market_data = [] # NEW: We will save all data here to show you later

for pair, data in market_data.items():
    data.ta.rsi(length=14, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)
    
    today = data.iloc[-1]
    current_price = today['Close']
    current_rsi = today['RSI_14']
    macd_fast = today['MACD_12_26_9']
    macd_slow = today['MACDs_12_26_9']
    sentiment = ai_sentiment_data.get(pair, 'NEUTRAL')
    
    signal = "IGNORE ⚪"
    
    # THE NEW RULEBOOK: Checking if the Override Switch is on or off
    if strict_mode:
        if current_rsi < rsi_oversold and (macd_fast > macd_slow) and sentiment == 'BULLISH':
            signal = "BUY 🟢"
        elif current_rsi > rsi_overbought and (macd_fast < macd_slow) and sentiment == 'BEARISH':
            signal = "SELL 🔴"
    else:
        # If Strict Mode is OFF, we ONLY look at the RSI sliders!
        if current_rsi < rsi_oversold:
            signal = "BUY 🟢"
        elif current_rsi > rsi_overbought:
            signal = "SELL 🔴"
            
    # Save for the "Actionable" table
    if signal != "IGNORE ⚪":
        actionable_trades.append({
            "Pair": pair, "Price": f"{current_price:.4f}", 
            "RSI": round(current_rsi, 1), "AI Sentiment": sentiment, "Action": signal
        })
        
    # NEW: Save EVERYTHING for the "Overview" table
    all_market_data.append({
        "Pair": pair, "Price": f"{current_price:.4f}", 
        "RSI": round(current_rsi, 1), "MACD Fast": round(macd_fast, 5), 
        "MACD Slow": round(macd_slow, 5), "AI Sentiment": sentiment
    })

# --- DISPLAY THE DASHBOARD ---

# 1. Actionable Trades Section
st.subheader("🎯 Actionable Trades")
if len(actionable_trades) > 0:
    st.success(f"Found {len(actionable_trades)} trade(s) based on your settings!")
    st.dataframe(pd.DataFrame(actionable_trades), use_container_width=True)
else:
    st.warning("No pairs met your criteria. (Try unchecking 'Strict Mode' in the sidebar!)")

st.markdown("---")

# 2. Market Overview Section
st.subheader("📊 Raw Market Overview")
st.markdown("Look at this data to see *why* the filters are ignoring certain pairs.")
st.dataframe(pd.DataFrame(all_market_data), use_container_width=True)
