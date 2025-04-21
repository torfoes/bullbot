#!/usr/bin/env python
"""
Command to list all current paper-traded option positions.
"""
from django.core.management.base import BaseCommand

from trading.models import OptionTrade


class Command(BaseCommand):
    help = 'List all paper-traded option positions.'

    def handle(self, *args, **options):
        trades = OptionTrade.objects.select_related('post').all()
        if not trades:
            self.stdout.write('No positions found.')
            return
        self.stdout.write('Current Option Trades:')
        for t in trades:
            post_id = getattr(t.post, 'tweet_id', 'N/A')
            self.stdout.write(
                f"{t.id}: Post {post_id}: {t.option_type} {t.ticker} @ {t.strike} exp {t.expiry} @ {t.entry_price}"
            )