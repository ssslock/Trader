from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from .models import Trader, Exchange, Market, Order, Balance
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
        context['high'] = market.high
        context['low'] = market.low
        context['bid'] = market.bid
        context['ask'] = market.ask
        context['volume'] = market.volume
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
        context['orders'] = trader.order_set.filter(state = 0)
        return context

def create_order(request, trader_id):
    trader = get_object_or_404(Trader, pk=trader_id)
    market = get_object_or_404(Market, symbol='ETH/BTC')
    try:
        balance_from = trader.balance_set.get(currency = market.currency_from)
        balance_to = trader.balance_set.get(currency = market.currency_to)
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
        if balance_from.value < volume:
            return render(request, 'traders/trader_detail.html', {
                'trader': trader,
                'error_message': "balance for %s not enough! has %f    needs %f" % (str(balance_from.currency), balance_from.value, volume),
            })
        else:
            balance_from.value -= volume
            balance_from.save()
    else:
        if balance_to.value < volume * price:
            return render(request, 'traders/trader_detail.html', {
                'trader': trader,
                'error_message': "balance for %s not enough! has %f    needs %f" % (str(balance_to.currency), balance_to.value, volume * price),
            })
        else:
            balance_to.value -= volume * price
            balance_to.save()
    order = Order(trader = trader, market = market, date = timezone.now(), bid = bid, price = price, volume = volume)
    order.save()
    return HttpResponseRedirect(reverse('traders:trader_detail', args=(trader_id,)))

def edit_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    trader = order.trader
    market = order.market
    balance_from = trader.balance_set.get(currency = market.currency_from)
    balance_to = trader.balance_set.get(currency = market.currency_to)
    if request.POST.get('deal'):
        if order.bid:
            balance_to.value += order.price * order.volume
            balance_to.save()
        else:
            balance_from.value += order.volume
            balance_from.save()
        order.state = 1
        order.save()
    else:
        if order.bid:
            balance_from.value += order.volume
            balance_from.save()
        else:
            balance_to.value += order.price * order.volume
            balance_to.save()
        order.state = -1
        order.save()
    return HttpResponseRedirect(reverse('traders:trader_detail', args=(trader.id,)))
    # trader = get_object_or_404(Trader, pk=trader_id)
    # market = get_object_or_404(Market, symbol='ETH/BTC')
    # try:
    #     balance_from = trader.balance_set.get(currency = market.currency_from)
    #     balance_to = trader.balance_set.get(currency = market.currency_to)
    # except:
    #     return render(request, 'traders/trader_detail.html', {
    #         'trader': trader,
    #         'error_message': "No balance for this market.",
    #     })
    # bid = request.POST.get('bid') != None
    # price = Decimal(request.POST['price'])
    # volume = Decimal(request.POST['volume'])
    # if price <= 0:
    #     return render(request, 'traders/trader_detail.html', {
    #         'trader': trader,
    #         'error_message': "price should be positive",
    #     })
    # if volume <= 0:
    #     return render(request, 'traders/trader_detail.html', {
    #         'trader': trader,
    #         'error_message': "volume should be positive",
    #     })
    # if bid:
    #     if balance_from.value < volume:
    #         return render(request, 'traders/trader_detail.html', {
    #             'trader': trader,
    #             'error_message': "balance for %s not enough! has %f    needs %f" % (str(balance_from.currency), balance_from.value, volume),
    #         })
    #     else:
    #         balance_from.value -= volume
    #         balance_from.save()
    # else:
    #     if balance_to.value < volume * price:
    #         return render(request, 'traders/trader_detail.html', {
    #             'trader': trader,
    #             'error_message': "balance for %s not enough! has %f    needs %f" % (str(balance_to.currency), balance_to.value, volume * price),
    #         })
    #     else:
    #         balance_to.value -= volume * price
    #         balance_to.save()
    # order = Order(trader = trader, market = market, date = timezone.now(), bid = bid, price = price, volume = volume)
    # order.save()
    # return HttpResponseRedirect(reverse('traders:trader_detail', args=(trader_id,)))

