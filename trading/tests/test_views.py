import datetime
from decimal import Decimal
import pytest
from django.urls import reverse
from django.test import Client
from django.utils import timezone

from trading.models import Post, OptionTrade


@pytest.mark.django_db
def test_positions_list_view():
    # Create sample post and trade
    post = Post.objects.create(
        tweet_id='200', user_handle='usr', text='sample text for view',
        timestamp=timezone.now(), sector='tech', sentiment='bullish'
    )
    trade = OptionTrade.objects.create(
        post=post, ticker='XLK', option_type='CALL', strike=Decimal('150'),
        entry_price=Decimal('10.00'), expiry=timezone.now().date()
    )
    client = Client()
    url = reverse('positions_list')
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    assert 'Paper-Traded Option Positions' in content
    assert 'sample text for view' in content
    assert 'XLK' in content
    assert '150' in content