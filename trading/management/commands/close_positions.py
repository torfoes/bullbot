#!/usr/bin/env python
"""
Command to close open OptionTrade positions when profitable.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
import yfinance as yf

from trading.models import OptionTrade


class Command(BaseCommand):
    help = 'Close open option trades when current intrinsic value exceeds entry price by profit_target.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--profit_target',
            type=float,
            default=0.1,
            help='Profit target as a decimal (e.g., 0.1 for 10%)',
        )

    def handle(self, *args, **options):
        profit_target = Decimal(str(options['profit_target']))
        open_trades = OptionTrade.objects.filter(exit_price__isnull=True)
        if not open_trades:
            self.stdout.write('No open trades to evaluate.')
            return
        for trade in open_trades:
            # Determine current option market price via yfinance option chain
            market_price = None
            try:
                ticker = yf.Ticker(trade.ticker)
                expiry_str = trade.expiry.strftime('%Y-%m-%d')
                opt_chain = ticker.option_chain(expiry_str)
                df = opt_chain.calls if trade.option_type == 'CALL' else opt_chain.puts
                # find matching strike
                match = df[df['strike'] == float(trade.strike)]
                if not match.empty:
                    market_price = Decimal(str(match['lastPrice'].iloc[-1]))
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f"Could not fetch option chain for {trade.ticker} ({e}); skipping current price lookup"
                ))
            # fallback to intrinsic if market_price unavailable
            if market_price is None:
                hist = yf.Ticker(trade.ticker).history(period='1d')
                if hist.empty:
                    self.stdout.write(self.style.WARNING(
                        f"No market data for {trade.ticker}, skipping {trade.id}"))
                    continue
                underlying = Decimal(hist['Close'].iloc[-1])
                if trade.option_type == 'CALL':
                    market_price = max(Decimal('0'), underlying - trade.strike)
                else:
                    market_price = max(Decimal('0'), trade.strike - underlying)
            # calculate profit percentage
            profit_pct = (market_price - trade.entry_price) / trade.entry_price
            threshold = profit_target
            if profit_pct >= threshold:
                trade.exit_price = market_price.quantize(Decimal('0.01'))
                trade.exit_timestamp = timezone.now()
                trade.save()
                self.stdout.write(self.style.SUCCESS(
                    f"Closed trade {trade.id}: entry={trade.entry_price}, exit={trade.exit_price}, P/L={profit_pct:.2%}"))
            else:
                self.stdout.write(
                    f"Trade {trade.id} not yet profitable (P/L={profit_pct:.2%}, threshold={threshold:.2%})"
                )