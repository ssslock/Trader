from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from .models import Trader, Exchange, Market, Order, Balance, Deal
from .api import get_api

class ExchangeListView(generic.ListView):
    template_name = 'traders/exchange_list.html'
    context_object_name = 'enabled_exchanges'

    def get_queryset(self):
        return Exchange.objects.filter(
            enabled=True
        ).order_by('id')[:10]

class ExchangeDetailView(generic.DetailView):
    model = Exchange
    template_name = 'traders/exchange_detail.html'

def update_exchange(request, exchange_id):
    exchange = get_object_or_404(Exchange, pk=exchange_id)
    try:
        exchange.update_info()
    except ():
        return HttpResponseRedirect(reverse('traders:exchange_detail', args=(exchange_id,)))
    else:
        return HttpResponseRedirect(reverse('traders:exchange_detail', args=(exchange_id,)))

class MarketDetailView(generic.DetailView):
    model = Market
    template_name = 'traders/market_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        market = context['market']
        market.update_info()
        context['datetime'] = market.last_update
        context['high'] = "%.10f" % market.high
        context['low'] = "%.10f" % market.low
        context['bid'] = "%.10f" % market.bid
        context['ask'] = "%.10f" % market.ask
        context['volume'] = "%.10f" % market.volume
        return context

class TraderListView(generic.ListView):
    template_name = 'traders/trader_list.html'
    context_object_name = 'active_traders'

    def get_queryset(self):
        return Trader.objects.filter(
            active=True
        ).order_by('id')[:10]

class TraderDetailView(generic.DetailView):
    model = Trader
    template_name = 'traders/trader_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trader = context['trader']
        context['orders'] = trader.order_set.filter(state = Order.STATE_CREATED)
        context['closed_orders'] = trader.order_set.filter(state = Order.STATE_CLOSED)
        return context

def create_order(request, trader_id):
    trader = get_object_or_404(Trader, pk=trader_id)
    market = get_object_or_404(Market, symbol='ETH/BTC')
    try:
        balance1 = trader.balance_set.get(currency = market.currency1)
        balance2 = trader.balance_set.get(currency = market.currency2)
    except:
        return render(request, 'traders/trader_detail.html', {
            'trader': trader,
            'error_message': "No balance for this market.",
        })
    bid = request.POST.get('bid') != None
    price = Decimal(request.POST['price'])
    volume = Decimal(request.POST['volume'])
    if price <= 0:
        return render(request, 'traders/trader_detail.html', {
            'trader': trader,
            'error_message': "price should be positive",
        })
    if volume <= 0:
        return render(request, 'traders/trader_detail.html', {
            'trader': trader,
            'error_message': "volume should be positive",
        })
    if bid:
        if balance1.available < volume:
            return render(request, 'traders/trader_detail.html', {
                'trader': trader,
                'error_message': "balance for %s not enough! has %f    needs %f" % (str(balance1.currency), balance1.available, volume),
            })
        else:
            balance1.available -= volume
            balance1.save()
    else:
        if balance2.available < volume * price:
            return render(request, 'traders/trader_detail.html', {
                'trader': trader,
                'error_message': "balance for %s not enough! has %f    needs %f" % (str(balance2.currency), balance2.available, volume * price),
            })
        else:
            balance2.available -= volume * price
            balance2.save()
    order = Order(trader = trader, market = market, create_date = timezone.now(), bid = bid, price = price, volume = volume, available = volume)
    order.save()
    return HttpResponseRedirect(reverse('traders:trader_detail', args=(trader_id,)))

def edit_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    trader = order.trader
    market = order.market
    balance1 = trader.balance_set.get(currency = market.currency1)
    balance2 = trader.balance_set.get(currency = market.currency2)
    if request.POST.get('deal'):
        volume = Decimal(request.POST.get('volume'))
        price = Decimal(request.POST.get('price'))
        volume2 = price * volume
        deal = Deal(order=order, date=timezone.now(), price=price, dealt1=volume, dealt2=volume2)
        deal.save()
        if order.bid:
            balance1.value -= volume
            balance2.value += volume2
            balance2.available += volume2
            balance1.save()
            balance2.save()
        else:
            balance1.value += volume
            balance1.available += volume
            balance2.value -= volume2
            balance1.save()
            balance2.save()
        order.available -= volume
        order.dealt1 += volume
        order.dealt2 += volume2
        if order.available <= 0:
            order.state = Order.STATE_CLOSED
            order.close_date = deal.date
        order.save()
    else:
        if order.bid:
            balance1.available += order.available
            balance1.save()
        else:
            balance2.available += order.price * order.volume
            balance2.save()
        order.state = Order.STATE_CLOSED
        order.close_date = timezone.now()
        order.save()
    return HttpResponseRedirect(reverse('traders:trader_detail', args=(trader.id,)))


class OrderDetailView(generic.DetailView):
    model = Order
    template_name = 'traders/order_detail.html'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     order = context['trader']
    #     context['orders'] = trader.order_set.filter(state = Order.STATE_CREATED)
    #     context['closed_orders'] = trader.order_set.filter(state = Order.STATE_CLOSED)
    #     return context