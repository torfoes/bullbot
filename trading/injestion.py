import logging, re, json, datetime as dt
import openai
from django.conf import settings
from truthbrush import Api as TruthScooper
from types import SimpleNamespace
from dateutil import parser as date_parse
from django.utils import timezone

log = logging.getLogger(__name__)
# OpenAI key is set per request in NLPService

SECTORS = ["defense", "energy", "healthcare", "technology", "finance", "industrials", "none"]

class TruthClient:
    """Fetch new posts from Truth Social via truthbrush.)"""
    def __init__(self):
        creds = settings.TRUTH_CREDENTIALS
        self.sc = TruthScooper(creds.get("username"), creds.get("password"))
        self.last_seen = None

    def get_new_posts(self):
        """
        Retrieve new posts since last_seen for the configured handle.
        Returns a list of SimpleNamespace(id, text, created_at, user_handle).
        """
        # Determine handle from settings
        handle = getattr(settings, 'TRUTH_HANDLE', 'realDonaldTrump')
        raw_items = self.sc.pull_statuses(handle)
        fresh = []
        for item in raw_items:
            # unify dict or object
            if isinstance(item, dict):
                raw_id = str(item.get('id'))
                text = item.get('content') or item.get('body') or item.get('text') or ''
                ts = item.get('created_at')
                try:
                    if isinstance(ts, str):
                        created_at = date_parse.parse(ts)
                    else:
                        created_at = timezone.now()
                except Exception:
                    created_at = timezone.now()
                user_handle = (item.get('account', {}) or {}).get('acct') or handle
            else:
                raw_id = str(item.id)
                text = getattr(item, 'text', '')
                created_at = getattr(item, 'created_at', timezone.now())
                user_handle = getattr(item, 'user_handle', handle)
            # stop if reached previously seen
            if self.last_seen and raw_id == self.last_seen:
                break
            status = SimpleNamespace(
                id=raw_id, text=text, created_at=created_at, user_handle=user_handle
            )
            fresh.append(status)
        # update last_seen to newest
        if fresh:
            self.last_seen = fresh[0].id
        # return oldest-first
        return list(reversed(fresh))

class NLPService:
    @staticmethod
    def _chat(prompt: str, max_tokens: int = 8):
        # configure API key at call time
        openai.api_key = settings.OPENAI_API_KEY
        resp = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()


    @classmethod
    def sector_and_sentiment(cls, text: str):
        # Return sector and sentiment on a 5-point scale
        prompt = (
            'Return JSON {"sector":<one of ' + ', '.join(SECTORS) + ", " +
            '"sentiment":<"strongly_bullish"|"bullish"|"neutral"|"bearish"|"strongly_bearish">} for the statement:\n\n'
            + text
        )
        raw = cls._chat(prompt, max_tokens=64)
        try:
            # extract JSON object across multiple lines
            match = re.search(r"\{.*?\}", raw, flags=re.DOTALL)
            if not match:
                raise ValueError(f"Invalid response: {raw}")
            data = json.loads(match.group(0))
            sector = data.get("sector", "none")
            sentiment = data.get("sentiment", "neutral")
            return sector, sentiment
        except Exception as e:
            log.error("parse error: %s", e)
            return "none", "neutral"

    # convenience pipeline: returns (sector, sentiment)
    @classmethod
    def process_post(cls, post_text: str):
        # Classify post into sector and sentiment (five-point scale)
        sector, sentiment = cls.sector_and_sentiment(post_text)
        return sector, sentiment