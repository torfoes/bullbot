#!/usr/bin/env python
"""
Command to classify a provided post text and suggest an option trade.
"""
from django.core.management.base import BaseCommand

from trading.injestion import NLPService
from trading.execution import decide_trade


class Command(BaseCommand):
    help = 'Classify a given post and show recommended option trade.'

    def add_arguments(self, parser):
        parser.add_argument(
            'text',
            type=str,
            help='Text of the post to classify',
        )

    def handle(self, *args, **options):
        text = options['text']
        self.stdout.write(f"Classifying text: {text}")
        # Classify post
        sector, sentiment = NLPService.process_post(text)
        strong = sentiment in ('strongly_bullish', 'strongly_bearish')
        self.stdout.write(f"Sector: {sector}")
        self.stdout.write(f"Sentiment: {sentiment}")
        if strong:
            trade_info = decide_trade(sector, sentiment)
            if trade_info:
                self.stdout.write("Suggested Trade:")
                for key, val in trade_info.items():
                    self.stdout.write(f"  {key}: {val}")
            else:
                self.stdout.write("No trade suggestion for these parameters.")
        else:
            self.stdout.write(f"Signal '{sentiment}' not strong enough; no trade executed.")