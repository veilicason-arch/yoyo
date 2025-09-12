#!/usr/bin/env python3
import sys
import json
import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def get_crypto_data(symbol: str, timeframe: str = '15m', period: str = '5d'):
    """Fetch crypto data from Yahoo Finance"""
    try:
        # Convert trading pair to Yahoo Finance format
        if not symbol.endswith('-USD'):
            symbol = symbol.replace('USDT', '-USD').replace('BUSD', '-USD')
        
        ticker = yf.Ticker(symbol)
        interval = '15m'  # Fixed to 15 minutes
        
        # Get historical data
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            return None
            
        return data
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}", file=sys.stderr)
        return None

def calculate_indicators(data: pd.DataFrame):
    """Calculate all technical indicators"""
    try:
        # RSI
        rsi = RSIIndicator(data['Close'], window=14).rsi()
        
        # EMA
        ema_short = EMAIndicator(data['Close'], window=12).ema_indicator()
        ema_long = EMAIndicator(data['Close'], window=26).ema_indicator()
        
        # Stochastic
        stoch = StochasticOscillator(
            high=data['High'], 
            low=data['Low'], 
            close=data['Close'],
            window=14,
            smooth_window=3
        )
        
        # MACD
        macd = MACD(data['Close'])
        
        # Bollinger Bands
        bb = BollingerBands(data['Close'], window=20)
        
        return {
            'rsi': rsi,
            'ema_short': ema_short,
            'ema_long': ema_long,
            'stoch_k': stoch.stoch(),
            'stoch_d': stoch.stoch_signal(),
            'macd': macd.macd(),
            'macd_signal': macd.macd_signal(),
            'bb_upper': bb.bollinger_hband(),
            'bb_middle': bb.bollinger_mavg(),
            'bb_lower': bb.bollinger_lband()
        }
    except Exception as e:
        print(f"Error calculating indicators: {e}", file=sys.stderr)
        return None

def generate_signal(data: pd.DataFrame, indicators: dict):
    """Generate trading signal based on technical indicators"""
    if len(data) < 50:
        return {
            'signal': 'HOLD',
            'confidence': 0,
            'reason': 'Insufficient data for analysis'
        }
    
    # Get latest values
    latest_rsi = indicators['rsi'].iloc[-1] if not indicators['rsi'].empty else 50
    latest_ema_diff = (indicators['ema_short'].iloc[-1] - indicators['ema_long'].iloc[-1]) if not indicators['ema_short'].empty else 0
    latest_stoch_k = indicators['stoch_k'].iloc[-1] if not indicators['stoch_k'].empty else 50
    latest_stoch_d = indicators['stoch_d'].iloc[-1] if not indicators['stoch_d'].empty else 50
    latest_macd = indicators['macd'].iloc[-1] if not indicators['macd'].empty else 0
    latest_macd_signal = indicators['macd_signal'].iloc[-1] if not indicators['macd_signal'].empty else 0
    
    current_price = data['Close'].iloc[-1]
    latest_bb_upper = indicators['bb_upper'].iloc[-1] if not indicators['bb_upper'].empty else current_price * 1.02
    latest_bb_lower = indicators['bb_lower'].iloc[-1] if not indicators['bb_lower'].empty else current_price * 0.98
    
    # Signal scoring system
    buy_signals = 0
    sell_signals = 0
    total_signals = 0
    
    # RSI Analysis (30% weight)
    if latest_rsi < 30:  # Oversold
        buy_signals += 3
    elif latest_rsi > 70:  # Overbought
        sell_signals += 3
    elif latest_rsi < 50:
        buy_signals += 1
    elif latest_rsi > 50:
        sell_signals += 1
    total_signals += 3
    
    # EMA Crossover (25% weight)
    if latest_ema_diff > 0:  # Short EMA above Long EMA
        buy_signals += 2.5
    else:
        sell_signals += 2.5
    total_signals += 2.5
    
    # Stochastic (20% weight)
    if latest_stoch_k < 20 and latest_stoch_d < 20:  # Oversold
        buy_signals += 2
    elif latest_stoch_k > 80 and latest_stoch_d > 80:  # Overbought
        sell_signals += 2
    elif latest_stoch_k > latest_stoch_d:  # K above D
        buy_signals += 1
    else:
        sell_signals += 1
    total_signals += 2
    
    # MACD (15% weight)
    if latest_macd > latest_macd_signal:  # MACD above signal
        buy_signals += 1.5
    else:
        sell_signals += 1.5
    total_signals += 1.5
    
    # Bollinger Bands (10% weight)
    if current_price < latest_bb_lower:  # Below lower band
        buy_signals += 1
    elif current_price > latest_bb_upper:  # Above upper band
        sell_signals += 1
    total_signals += 1
    
    # Calculate confidence and determine signal
    buy_confidence = (buy_signals / total_signals) * 100
    sell_confidence = (sell_signals / total_signals) * 100
    
    if buy_confidence > 60:
        signal = 'BUY'
        confidence = int(buy_confidence)
        reason = f"Strong bullish indicators: RSI={latest_rsi:.1f}, EMA trend positive"
    elif sell_confidence > 60:
        signal = 'SELL'
        confidence = int(sell_confidence)
        reason = f"Strong bearish indicators: RSI={latest_rsi:.1f}, EMA trend negative"
    else:
        signal = 'HOLD'
        confidence = int(max(buy_confidence, sell_confidence))
        reason = "Mixed signals, market consolidation"
    
    return {
        'signal': signal,
        'confidence': confidence,
        'reason': reason,
        'indicators': {
            'rsi': round(latest_rsi, 2),
            'ema_short': round(indicators['ema_short'].iloc[-1], 4) if not indicators['ema_short'].empty else None,
            'ema_long': round(indicators['ema_long'].iloc[-1], 4) if not indicators['ema_long'].empty else None,
            'stoch_k': round(latest_stoch_k, 2),
            'stoch_d': round(latest_stoch_d, 2),
            'macd': round(latest_macd, 6),
            'macd_signal': round(latest_macd_signal, 6),
            'current_price': round(current_price, 4)
        }
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Trading pair is required'}))
        sys.exit(1)
    
    pair = sys.argv[1].upper()
    timeframe = sys.argv[2] if len(sys.argv) > 2 else '15m'
    
    try:
        # Fetch crypto data
        crypto_data = get_crypto_data(pair, timeframe)
        
        if crypto_data is None or crypto_data.empty:
            print(json.dumps({
                'error': f'Unable to fetch data for {pair}',
                'pair': pair,
                'timeframe': timeframe
            }))
            sys.exit(1)
        
        # Calculate indicators
        indicators = calculate_indicators(crypto_data)
        
        if indicators is None:
            print(json.dumps({
                'error': 'Failed to calculate technical indicators',
                'pair': pair
            }))
            sys.exit(1)
        
        # Generate signal
        signal_data = generate_signal(crypto_data, indicators)
        
        # Prepare response
        response = {
            'pair': pair,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat(),
            'signal': signal_data['signal'],
            'confidence': signal_data['confidence'],
            'reason': signal_data['reason'],
            'indicators': signal_data['indicators'],
            'last_price': round(crypto_data['Close'].iloc[-1], 4),
            'volume': int(crypto_data['Volume'].iloc[-1]) if 'Volume' in crypto_data.columns else None,
            'price_change_24h': round(
                ((crypto_data['Close'].iloc[-1] - crypto_data['Close'].iloc[-96]) / crypto_data['Close'].iloc[-96]) * 100, 2
            ) if len(crypto_data) >= 96 else None
        }
        
        print(json.dumps(response))
        
    except Exception as e:
        print(json.dumps({'error': f'Analysis failed: {str(e)}'}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()