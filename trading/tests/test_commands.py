import datetime
from decimal import Decimal

import pandas as pd
import yfinance as yf
import pytest
from django.core.management import call_command
from io import StringIO

from trading.injestion import NLPService
from trading.execution import decide_trade
from trading.models import Post, OptionTrade
from django.utils import timezone


class DummyTicker:
    def __init__(self, symbol):
        pass
    def history(self, period):
        return pd.DataFrame({'Close': [123.45]})


@pytest.mark.django_db
def test_classify_post_command(monkeypatch, capsys):
    # Stub NLPService to return a weak bearish (no trade)
    # Stub NLPService to return weak bearish sentiment (no trade)
    monkeypatch.setattr(NLPService, 'process_post', staticmethod(lambda t: ('technology', 'bearish')))
    # Stub yfinance
    monkeypatch.setattr(yf, 'Ticker', DummyTicker)
    out = StringIO()
    # Run command
    call_command('classify_post', 'Example post', stdout=out)
    output = out.getvalue()
    # Basic output checks
    assert 'Classifying text: Example post' in output
    assert 'Sector: technology' in output
    assert 'Sentiment: bearish' in output
    # Weak signal should not suggest trade
    assert "Signal 'bearish' not strong enough; no trade executed." in output

@pytest.mark.django_db
def test_classify_post_strong(monkeypatch):
    # Stub NLPService to return strong bullish
    # Stub NLPService to return strong bullish sentiment
    monkeypatch.setattr(NLPService, 'process_post', staticmethod(lambda t: ('technology', 'strongly_bullish')))
    monkeypatch.setattr(yf, 'Ticker', DummyTicker)
    out = StringIO()
    call_command('classify_post', 'Example post', stdout=out)
    output = out.getvalue()
    # Strong signal should suggest a trade
    assert 'Sector: technology' in output
    assert 'Sentiment: strongly_bullish' in output
    assert 'Suggested Trade:' in output
    assert 'option_type: CALL' in output

@pytest.mark.django_db
def test_list_positions_command(monkeypatch, capsys):
    # Create posts and trades
    p1 = Post.objects.create(
        tweet_id='10', user_handle='u', text='t', timestamp=timezone.now(),
        sector='energy', sentiment='bullish'
    )
    t1 = OptionTrade.objects.create(
        post=p1, ticker='XLE', option_type='CALL', strike=Decimal('100'),
        expiry=datetime.date.today(), entry_price=Decimal('50')
    )
    p2 = Post.objects.create(
        tweet_id='20', user_handle='u2', text='t2', timestamp=timezone.now(),
        sector='finance', sentiment='bearish'
    )
    t2 = OptionTrade.objects.create(
        post=p2, ticker='XLF', option_type='PUT', strike=Decimal('200'),
        expiry=datetime.date.today(), entry_price=Decimal('20')
    )
    out = StringIO()
    call_command('list_positions', stdout=out)
    output = out.getvalue()
    assert 'Current Option Trades:' in output
    # Verify each trade line includes its ID, post ID, option type, and ticker
    assert f"{t1.id}: Post 10:" in output
    assert "CALL XLE" in output
    assert "@ 100" in output
    assert f"{t2.id}: Post 20:" in output
    assert "PUT XLF" in output
    assert "@ 200" in output