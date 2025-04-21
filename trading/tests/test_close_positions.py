from decimal import Decimal
import pandas as pd
import pytest
import yfinance as yf
from django.core.management import call_command
from django.utils import timezone
from io import StringIO

from trading.models import OptionTrade, Post


class DummyTickerCP:
    def __init__(self, symbol):
        self.symbol = symbol
    def history(self, period):
        # For symbol 'XLE', return price 25; others default
        if self.symbol == 'XLE':
            return pd.DataFrame({'Close': [25.0]})
        return pd.DataFrame({'Close': [5.0]})


@pytest.mark.django_db
def test_close_profitable(monkeypatch):
    # stub yfinance
    monkeypatch.setattr(yf, 'Ticker', DummyTickerCP)
    # create post and open trade
    post = Post.objects.create(
        tweet_id='100', user_handle='u', text='t', timestamp=timezone.now(),
        sector='energy', sentiment='bullish'
    )
    trade = OptionTrade.objects.create(
        post=post, ticker='XLE', option_type='CALL', strike=Decimal('10'),
        entry_price=Decimal('5'), expiry=timezone.now().date()
    )
    out = StringIO()
    call_command('close_positions', '--profit_target', '0.5', stdout=out)
    output = out.getvalue()
    # Check closed message
    assert f"Closed trade {trade.id}" in output
    trade.refresh_from_db()
    assert trade.exit_price == Decimal('15.00')
    assert trade.exit_timestamp is not None


@pytest.mark.django_db
def test_close_not_profitable(monkeypatch):
    monkeypatch.setattr(yf, 'Ticker', DummyTickerCP)
    post = Post.objects.create(
        tweet_id='101', user_handle='u', text='t', timestamp=timezone.now(),
        sector='energy', sentiment='bullish'
    )
    # underlying price=5, strike=10, intrinsic=0; entry_price=10
    trade = OptionTrade.objects.create(
        post=post, ticker='XLF', option_type='PUT', strike=Decimal('10'),
        entry_price=Decimal('10'), expiry=timezone.now().date()
    )
    out = StringIO()
    call_command('close_positions', '--profit_target', '0.1', stdout=out)
    output = out.getvalue()
    assert f"Trade {trade.id} not yet profitable" in output
    trade.refresh_from_db()
    assert trade.exit_price is None
    assert trade.exit_timestamp is None


@pytest.mark.django_db
def test_close_no_trades(tmp_path, capsys):
    # remove all trades
    OptionTrade.objects.all().delete()
    out = StringIO()
    call_command('close_positions', stdout=out)
    output = out.getvalue().strip()
    assert output == 'No open trades to evaluate.'