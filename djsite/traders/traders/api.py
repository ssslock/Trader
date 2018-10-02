
from .models import Trader, Exchange, Market, Currency

def get_exchange(exchange_name):
    exchange = Exchange.objects.get(name=exchange_name)
    # try:
    #     exchange = Exchange.objects.get(name=exchange_name)
    # except Exchange.DoesNotExist:
    #     return None
    # else:
    #     return exchange

def get_currency(exchange, currency_name):
    currency = exchange.currency_set.get(name=currency_name)

