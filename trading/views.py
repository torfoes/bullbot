
from django.shortcuts import render
from trading.models import OptionTrade

def positions_list(request):
    """Render a table of paper-traded option positions and their causes."""
    trades = OptionTrade.objects.select_related('post').all()
    return render(request, 'positions.html', {'trades': trades})

# Create your views here.
