#!/usr/bin/env python
"""
Django management command to run the bullbot pipeline:
ingest Truth Social posts, classify with OpenAI, decide trades, and simulate paper options.
"""
import time
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils import timezone

from trading.execution import Simulator
from trading.models import Post


class Command(BaseCommand):
    help = 'Fetch Truth Social posts, classify, and paper-trade options based on NLP signals.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run one iteration and exit',
        )

    def handle(self, *args, **options):
        # Instantiate ingestion and NLP services from settings
        ingestion_cls = import_string(settings.INGESTION_CLASS)
        nlp_cls = import_string(settings.NLP_SERVICE_CLASS)
        tc = ingestion_cls()
        simulator = Simulator()
        once = options.get('once', False)
        self.stdout.write(self.style.NOTICE('Starting bullbot pipeline...'))
        while True:
            posts = tc.get_new_posts()
            for p in posts:
                self.stdout.write(f"Processing post {p.id} at {getattr(p, 'created_at', '')}")
                # Classify post: get sector and sentiment
                sector, sentiment = nlp_cls.process_post(p.text)
                # Persist post
                post, created = Post.objects.get_or_create(
                    tweet_id=p.id,
                    defaults={
                        'user_handle': getattr(p, 'user_handle', ''),
                        'text': p.text,
                        'timestamp': getattr(p, 'created_at', timezone.now()),
                        'sector': sector,
                        'sentiment': sentiment,
                    }
                )
                # Only execute trades on strong signals
                strong = sentiment in ('strongly_bullish', 'strongly_bearish')
                if strong:
                    trade = simulator.create_trade(post)
                    if trade:
                        self.stdout.write(self.style.SUCCESS(f"Simulated trade: {trade}"))
                    else:
                        self.stdout.write(self.style.WARNING(
                            "Trade simulation returned no result (check execution logic)"
                        ))
                else:
                    # Weak or neutral signals: no trade executed
                    self.stdout.write(self.style.WARNING(
                        f"Signal '{sentiment}' not strong enough; no trade executed"
                    ))
            if once:
                self.stdout.write(self.style.NOTICE('Completed one iteration, exiting.'))
                break
            # sleep before next poll
            time.sleep(getattr(settings, 'POLL_INTERVAL', 60))
