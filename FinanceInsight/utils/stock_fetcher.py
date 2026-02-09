import yfinance as yf
from FinanceInsight.models import StockRecommendation
from decimal import Decimal
import logging
import ssl
import os
import urllib3
import random

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context
os.environ['PYTHONHTTPSVERIFY'] = '0'

logger = logging.getLogger(__name__)

def update_all_stock_prices():
    """Update current price and change percentage for all recommended stocks."""
    stocks = StockRecommendation.objects.all()
    results = {'success': 0, 'failed': 0, 'simulated': 0}
    
    for stock in stocks:
        try:
            symbol = _get_yfinance_symbol(stock)
            print(f"Updating {stock.stock_name} ({symbol})...")
            
            ticker = yf.Ticker(symbol)
            current_price = None
            prev_close = None
            
            # Strategy 1: Attempt fast_info (Real-time approx)
            try:
                # Force refresh if possible (yfinance objects are lazy)
                info = ticker.fast_info
                last_price = info.last_price
                p_close = info.previous_close
                if last_price and p_close:
                    current_price = Decimal(str(last_price))
                    prev_close = Decimal(str(p_close))
            except Exception as e:
                print(f"fast_info failed for {symbol}: {e}")
            
            # Strategy 2: Attempt history (Fallback)
            if current_price is None:
                try:
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        last_row = hist.iloc[-1]
                        current_price = Decimal(str(last_row['Close']))
                        # Estimate prev close (Open or previous day? fast_info is better for change)
                        # If we have only 1d, reliable change is hard.
                        # Try getting 2d to be sure?
                        hist_2d = ticker.history(period="2d")
                        if len(hist_2d) >= 2:
                            prev_close = Decimal(str(hist_2d.iloc[-2]['Close']))
                        else:
                             # Fallback to Open if no previous day (e.g. IPO or just listing)
                            prev_close = Decimal(str(last_row['Open']))
                except Exception as e:
                   print(f"history failed for {symbol}: {e}")

            if current_price and prev_close:
                change = current_price - prev_close
                # Avoid division by zero
                if prev_close != 0:
                    change_percent = (change / prev_close) * 100
                else:
                    change_percent = Decimal(0)
                
                stock.current_price = current_price
                stock.price_change = change
                stock.price_change_percent = change_percent
                stock.save()
                
                results['success'] += 1
            else:
                 print(f"No data available for {symbol}")
                 results['failed'] += 1
                    
        except Exception as e:
            print(f"Fatal error updating {stock.stock_name}: {e}")
            results['failed'] += 1
            
    return results

def _get_yfinance_symbol(stock):
    """Convert DB stock code to yfinance symbol format."""
    code = stock.stock_code.strip()
    market_code = stock.market.code
    
    if market_code == 'TWSE':
        return f"{code}.TW"
    elif market_code == 'TPEX': # Taipei Exchange (OTC)
        return f"{code}.TWO"
    else:
        # US stocks usually don't need suffix
        return code
