"""
Execution logic: price fetching, decision rules, and simulation.
"""
import datetime
from decimal import Decimal, ROUND_HALF_UP
import yfinance as yf

from .models import OptionTrade, Post

# Map detected sector to representative ETF ticker
SECTOR_TICKER = {
    'defense': 'ITA',
    'energy': 'XLE',
    'healthcare': 'XLV',
    'technology': 'XLK',
    'finance': 'XLF',
    'industrials': 'XLI',
    'none': None,
}

def next_friday(from_date: datetime.date) -> datetime.date:
    """Return the next Friday after the given date."""
    days_ahead = 4 - from_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return from_date + datetime.timedelta(days=days_ahead)

def decide_trade(sector: str, sentiment: str) -> dict | None:
    """
    Decide on an option trade based on sector and sentiment.
    Returns dict with keys: ticker, option_type, strike, expiry, entry_price.
    """
    # Only strong sentiments trigger trades
    sent_low = sentiment.lower()
    if sent_low not in ('strongly_bullish', 'strongly_bearish'):
        return None
    ticker = SECTOR_TICKER.get(sector)
    if not ticker:
        return None
    # Determine option type
    opt_type = 'CALL' if 'bullish' in sent_low else 'PUT'
    # ATM strike: nearest integer
    # Fetch or calculate strike price based on underlying
    # First, try underlying price for strike
    yf_ticker = yf.Ticker(ticker)
    hist = yf_ticker.history(period='1d')
    if hist.empty:
        return None
    underlying_price = Decimal(hist['Close'].iloc[-1])
    strike = underlying_price.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    # Expiry is next Friday
    expiry = next_friday(datetime.date.today())
    # Attempt to fetch option prices (bid/ask)
    bid, ask = None, None
    try:
        opt_chain = yf_ticker.option_chain(expiry.strftime('%Y-%m-%d'))
        df = opt_chain.calls if opt_type == 'CALL' else opt_chain.puts
        match = df[df['strike'] == float(strike)]
        if not match.empty:
            bid = Decimal(str(match['bid'].iloc[-1]))
            ask = Decimal(str(match['ask'].iloc[-1]))
    except Exception:
        # option_chain may not be available, fallback
        pass
    # Determine entry price: buy at ask, or fallback to intrinsic
    if ask is not None and ask > 0:
        entry_price = ask
    else:
        # intrinsic value
        entry_price = max(Decimal('0'), underlying_price - strike) if opt_type == 'CALL' else max(Decimal('0'), strike - underlying_price)
    return {
        'ticker': ticker,
        'option_type': opt_type,
        'strike': strike,
        'expiry': expiry,
        'entry_price': entry_price,
        'entry_bid': bid,
        'entry_ask': ask,
    }

class Simulator:
    """Simulate paper trades by writing OptionTrade rows."""
    @staticmethod
    def create_trade(post: Post) -> OptionTrade | None:
        info = decide_trade(post.sector, post.sentiment)
        if not info:
            return None
        trade = OptionTrade.objects.create(
            post=post,
            ticker=info['ticker'],
            option_type=info['option_type'],
            strike=info['strike'],
            expiry=info['expiry'],
            entry_price=info['entry_price'],
        )
        return trade