from django.contrib import admin

# Register your models here.
from .models import Wallet, Strategy, AlgoModel, Token, PriceFeed

admin.site.register(Wallet)
admin.site.register(Strategy)
admin.site.register(AlgoModel)
admin.site.register(Token)
admin.site.register(PriceFeed)