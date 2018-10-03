from django.db import models

from .api import get_api
from django.utils import timezone

# 交易所
class Exchange(models.Model):
    name = models.CharField(max_length=200)
    enabled = models.BooleanField(default=True)
    # connected = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    def update_info(self):
        api = get_api(self.name)
        for symbol in api.markets.keys():
            if symbol.find('.d') >= 0:
                continue
            self.get_or_create_market(symbol)
    
    def get_or_create_currency(self, currency_name):
        try:
            currency = self.currency_set.get(name=currency_name)
        except Currency.DoesNotExist:
            currency = Currency(exchange=self, name=currency_name)
            currency.save()
        return currency
    
    def get_currency(self, currency_name):
        return self.currency_set.get(name=currency_name)

    def get_or_create_market(self, symbol):
        try:
            market = self.market_set.get(symbol=symbol)
        except Market.DoesNotExist:
            splitter = symbol.find('/')
            currency1 = self.get_or_create_currency(symbol[:splitter])
            currency2 = self.get_or_create_currency(symbol[splitter + 1:])
            market = Market(exchange=self, currency1 = currency1, currency2 = currency2, symbol=symbol, last_update = timezone.now())
            market.save()
        return market


# 交易所币种
class Currency(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    name = models.CharField(max_length=16)

    def __str__(self):
        return "%s/%s" % (self.exchange.name, self.name)

# 交易所市场
class Market(models.Model):
    exchange = models.ForeignKey(Exchange, on_delete=models.CASCADE)
    symbol = models.CharField(max_length=16)
    active = models.BooleanField(default=True)
    currency1 = models.ForeignKey(Currency, on_delete=models.SET_NULL, related_name="cfrom", null=True)
    currency2 = models.ForeignKey(Currency, on_delete=models.SET_NULL, related_name="cto", null=True)

    last_update = models.DateTimeField()
    high = models.DecimalField(default=0, max_digits=40, decimal_places=20)
    low = models.DecimalField(default=0, max_digits=40, decimal_places=20)
    bid = models.DecimalField(default=0, max_digits=40, decimal_places=20)
    ask = models.DecimalField(default=0, max_digits=40, decimal_places=20)
    volume = models.DecimalField(default=0, max_digits=40, decimal_places=20)

    def __str__(self):
        return '%s %s' % (str(self.exchange), self.symbol)
    
    def update_info(self):
        api = get_api(self.exchange.name)
        if api.has['fetchTicker']:
            ticker = api.fetch_ticker(self.symbol)
            self.last_update = ticker['datetime']
            self.high = ticker['high']
            self.low = ticker['low']
            self.bid = ticker['bid']
            self.ask = ticker['ask']
            self.volume = ticker['quoteVolume']
            self.save()


# 交易策略
class Trader(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# 策略余额
class Balance(models.Model):
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    value = models.DecimalField(default=0, max_digits=40, decimal_places=20)
    available = models.DecimalField(default=0, max_digits=40, decimal_places=20)
    
    def __str__(self):
        return '%s : %.10f' % (str(self.currency), self.value)
    
    def detail_str(self):
        return '%s   balance: %.10f   available: %.10f' % (str(self.currency), self.value, self.available)

# 订单
class Order(models.Model):
    STATE_CREATED = 0
    STATE_CLOSED = 1
    trader = models.ForeignKey(Trader, on_delete=models.CASCADE)
    market = models.ForeignKey(Market, on_delete=models.CASCADE)
    create_date = models.DateTimeField()
    close_date = models.DateTimeField(null=True)
    bid = models.BooleanField()
    price = models.DecimalField(max_digits=40, decimal_places=20)
    volume = models.DecimalField(max_digits=40, decimal_places=20)
    available = models.DecimalField(max_digits=40, decimal_places=20)
    dealt1 = models.DecimalField(default=0,max_digits=40, decimal_places=20)
    dealt2 = models.DecimalField(default=0,max_digits=40, decimal_places=20)
    state = models.SmallIntegerField(default=0)

    def __str__(self):
        if self.bid:
            return '%s %s bid' % (str(self.create_date), str(self.market))
        else:
            return '%s %s ask' % (str(self.create_date), str(self.market))

    def detail_str(self):
        if self.bid:
            return '%s %s bid   price: %.10f  volume: %.10f' % (str(self.create_date), str(self.market), self.price, self.volume)
        else:
            return '%s %s ask   price: %.10f  volume:, %.10f' % (str(self.create_date), str(self.market), self.price, self.volume)
# 交易
class Deal(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    date = models.DateTimeField()
    price = models.DecimalField(max_digits=40, decimal_places=20)
    dealt1 = models.DecimalField(max_digits=40, decimal_places=20)
    dealt2 = models.DecimalField(max_digits=40, decimal_places=20)
    
    def __str__(self):
        '%s %.10f' % (str(self.create_date), self.volume)

    def detail_str(self):
        if self.order.bid:
            return '%s %.10f %.10f %s for %.10f %s' % (str(self.date), self.dealt1, self.dealt1, self.order.market.currency1.name, self.dealt2, self.order.market.currency2.name)
        else:
            return '%s %.10f %.10f %s for %.10f %s' % (str(self.date), self.dealt1, self.dealt2, self.order.market.currency2.name, self.dealt1, self.order.market.currency1.name)