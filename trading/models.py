from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    NETWORK_CHOICES = [
        ("ethereum", "Ethereum Mainnet"),
        ("arbitrum", "Arbitrum"),
        ("optimism", "Optimism"),
        ("polygon", "Polygon"),
        ("base", "Base"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    network = models.CharField(max_length=50, choices=NETWORK_CHOICES)
    address = models.CharField(max_length=100)
    private_key_encrypted = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.network} - {self.address}"



class Strategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="strategies")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_live = models.BooleanField(default=False)
    initial_capital = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    base_asset = models.CharField(max_length=50, default="USDC")
    parameters = models.JSONField(default=dict, blank=True)  # flexible for storing thresholds, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Strategy: {self.name} (User: {self.user.username})"



class AlgoModel(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="algomodels")
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50, default="1.0")
    model_file_path = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (v{self.version}) for {self.strategy.name}"


class Token(models.Model):
    NETWORK_CHOICES = [
        ("ethereum", "Ethereum"),
        ("arbitrum", "Arbitrum"),
        ("optimism", "Optimism"),
        ("polygon", "Polygon"),
        # add more networks as needed
    ]

    symbol = models.CharField(max_length=20)
    address = models.CharField(max_length=100)
    decimals = models.IntegerField(default=18)
    network = models.CharField(max_length=50, choices=NETWORK_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.symbol} ({self.network})"


# 5. PriceFeed Model (Historical OHLCV data)
class PriceFeed(models.Model):
    SOURCE_CHOICES = [
        ("uniswap_v3", "Uniswap V3"),
        ("1inch", "1inch Aggregator"),
        ("chainlink", "Chainlink Oracle"),
        ("paraswap", "ParaSwap"),
        # etc.
    ]

    token = models.ForeignKey(Token, on_delete=models.CASCADE, related_name="price_feeds")
    timestamp = models.DateTimeField()
    open = models.DecimalField(max_digits=20, decimal_places=8)
    high = models.DecimalField(max_digits=20, decimal_places=8)
    low = models.DecimalField(max_digits=20, decimal_places=8)
    close = models.DecimalField(max_digits=20, decimal_places=8)
    volume = models.DecimalField(max_digits=30, decimal_places=8, default=0)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default="uniswap_v3")

    class Meta:
        unique_together = ("token", "timestamp", "source")

    def __str__(self):
        return f"{self.token.symbol} at {self.timestamp}"


class Tweet(models.Model):
    tweet_id = models.CharField(max_length=50, unique=True)
    user_handle = models.CharField(max_length=100)
    text = models.TextField()
    timestamp = models.DateTimeField()
    inserted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tweet {self.tweet_id} by {self.user_handle}"


class SentimentScore(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name="sentiment_scores")
    sentiment_value = models.FloatField()  # e.g. -1 to 1
    model_version = models.CharField(max_length=50, default="1.0")
    scored_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sentiment: {self.sentiment_value} for Tweet {self.tweet.tweet_id}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("FILLED", "Filled"),
        ("CANCELLED", "Cancelled"),
        ("FAILED", "Failed"),
    ]
    ORDER_TYPE_CHOICES = [
        ("MARKET", "Market"),
        ("LIMIT", "Limit"),
    ]

    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="orders")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    token_in = models.ForeignKey(Token, on_delete=models.CASCADE, related_name="orders_in")
    token_out = models.ForeignKey(Token, on_delete=models.CASCADE, related_name="orders_out")
    amount_in = models.DecimalField(max_digits=30, decimal_places=8)
    price_limit = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default="MARKET")
    is_paper_trade = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} for {self.strategy.name} ({self.status})"


class Trade(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="trade")
    tx_hash = models.CharField(max_length=100, null=True, blank=True)
    price_executed = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    amount_out = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    execution_timestamp = models.DateTimeField(auto_now_add=True)
    gas_used = models.DecimalField(max_digits=30, decimal_places=8, null=True, blank=True)
    gas_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)

    def __str__(self):
        return f"Trade for Order {self.order.id}"


class StrategyPerformance(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="performances")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    net_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    net_profit_pct = models.DecimalField(max_digits=7, decimal_places=4, default=0)  # e.g. 12.34%
    drawdown_pct = models.DecimalField(max_digits=7, decimal_places=4, default=0)
    sharpe_ratio = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    sortino_ratio = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    num_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # e.g. 53.33
    other_metrics = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Performance for {self.strategy.name} from {self.start_time} to {self.end_time or 'ongoing'}"


class BridgeTransaction(models.Model):
    STATUS_CHOICES = [
        ("INITIATED", "Initiated"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]

    NETWORK_CHOICES = [
        ("ethereum", "Ethereum Mainnet"),
        ("arbitrum", "Arbitrum"),
        ("optimism", "Optimism"),
        ("polygon", "Polygon"),
    ]

    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="bridge_txs")
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    from_network = models.CharField(max_length=50, choices=NETWORK_CHOICES)
    to_network = models.CharField(max_length=50, choices=NETWORK_CHOICES)
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=30, decimal_places=8)
    bridge_tx_hash = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="INITIATED")

    def __str__(self):
        return f"Bridge {self.id} {self.from_network} -> {self.to_network}"


# 10. Alerts & Events
class Alert(models.Model):
    ALERT_TYPE_CHOICES = [
        ("PRICE_THRESHOLD", "Price Threshold"),
        ("SENTIMENT_SPIKE", "Sentiment Spike"),
        ("ARBITRAGE_OPP", "Arbitrage Opportunity"),
    ]

    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name="alerts", null=True, blank=True)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    trigger_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert: {self.alert_type} for strategy {self.strategy.name if self.strategy else 'Global'}"


class SystemLog(models.Model):
    LOG_LEVEL_CHOICES = [
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
    ]

    message = models.TextField()
    level = models.CharField(max_length=20, choices=LOG_LEVEL_CHOICES, default="INFO")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.level}] - {self.message}"
