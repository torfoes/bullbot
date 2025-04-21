import datetime
from decimal import Decimal
import pandas as pd
import yfinance as yf
import pytest
from types import SimpleNamespace

from trading.execution import decide_trade


class DummyChainTicker:
    def __init__(self, symbol):
        self.symbol = symbol
    def history(self, period):
        # not used in chain test
        return pd.DataFrame({'Close': [100.0]})
    def option_chain(self, expiry):
        # build calls and puts DataFrames with bid/ask
        data = {
            'strike': [100.0, 101.0, 102.0],
            'bid': [1.0, 2.0, 3.0],
            'ask': [1.5, 2.5, 3.5],
        }
        df = pd.DataFrame(data)
        return SimpleNamespace(calls=df, puts=df)

@pytest.mark.parametrize('sentiment', ['strongly_bullish', 'strongly_bearish'])
def test_decide_trade_option_chain(monkeypatch, sentiment):
    # Stub yfinance Ticker to DummyChainTicker
    monkeypatch.setattr(yf, 'Ticker', DummyChainTicker)
    # force sector->ticker mapping
    # assume sector 'energy' maps to ticker
    # patch mapping for test
    from trading.execution import SECTOR_TICKER
    SECTOR_TICKER['test'] = 'XLE'
    # choose sentiment
    # monkeypatch next_friday to return fixed date
    from trading.execution import next_friday
    monkeypatch.setattr('trading.execution.next_friday', lambda d: datetime.date.today())
    # call decide_trade
    info = decide_trade('test', sentiment)
    # entry_price should match ask for ATM strike (first index)
    assert info['entry_price'] == Decimal('1.50')