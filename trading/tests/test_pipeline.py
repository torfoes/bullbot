import datetime
from decimal import Decimal

import pandas as pd
import yfinance as yf
from django.test import TestCase
from django.utils import timezone

from trading.injestion import TruthClient, NLPService
from io import StringIO
from trading.execution import decide_trade, Simulator
from trading.models import Post, OptionTrade

class DummyStatus:
    def __init__(self, id, text, created_at=None):
        self.id = id
        self.text = text
        self.created_at = created_at or timezone.now()
        self.user_handle = 'realDonaldTrump'

class PipelineTest(TestCase):
    def setUp(self):
        # Return a single new post
        TruthClient.get_new_posts = lambda self: [DummyStatus('1','Test')]
        # Stub NLPService to return strong bullish sentiment
        NLPService.process_post = staticmethod(lambda text: ('energy', 'strongly_bullish'))
        class DummyTicker:
            def __init__(self,s): pass
            def history(self, period): return pd.DataFrame({'Close':[100.0]})
        yf.Ticker = DummyTicker
    def test_pipeline(self):
        # Running the bot should create a CALL trade for strong bullish
        from django.core.management import call_command
        call_command('run_bot', '--once')
        post = Post.objects.get(tweet_id='1')
        self.assertEqual(post.sector, 'energy')
        self.assertEqual(post.sentiment, 'strongly_bullish')
        trade = OptionTrade.objects.get(post=post)
        self.assertEqual(trade.option_type, 'CALL')

    def test_pipeline_weak_signal(self):
        # Stub NLPService to weak bearish sentiment
        NLPService.process_post = staticmethod(lambda text: ('energy', 'bearish'))
        from django.core.management import call_command
        out = StringIO()
        # Run pipeline; no trade for weak signal
        call_command('run_bot', '--once', stdout=out)
        with self.assertRaises(OptionTrade.DoesNotExist):
            OptionTrade.objects.get(post__tweet_id='1')

class ExecutionTest(TestCase):
    def test_decide_trade_weak(self):
        # weak bearish should not produce a trade
        class DummyTicker2:
            def __init__(self, s): pass
            def history(self, period): return pd.DataFrame({'Close': [50.75]})
        yf.Ticker = DummyTicker2
        self.assertIsNone(decide_trade('finance', 'bearish'))

    def test_decide_trade_strong_put(self):
        # strong bearish should produce a PUT
        class DummyTicker3:
            def __init__(self, s): pass
            def history(self, period): return pd.DataFrame({'Close': [50.75]})
            def option_chain(self, expiry):
                df = pd.DataFrame({'strike': [51.0], 'bid': [2.0], 'ask': [2.5]})
                return SimpleNamespace(calls=df, puts=df)
        yf.Ticker = DummyTicker3
        from types import SimpleNamespace
        # patch next_friday
        import trading.execution as tx
        tx.next_friday = lambda d: datetime.date.today()
        info = decide_trade('finance', 'strongly_bearish')
        self.assertEqual(info['option_type'], 'PUT')
        self.assertEqual(info['entry_price'], Decimal('2.50'))