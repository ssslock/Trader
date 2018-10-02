from django.urls import path

from . import views

app_name = 'traders'
urlpatterns = [
    path('', views.ExchangeListView.as_view(), name='index'),
    # path('', views.TraderListView.as_view(), name='index'),
    path('exchanges/', views.ExchangeListView.as_view(), name='exchange_list'),
    path('exchange/<int:pk>/', views.ExchangeDetailView.as_view(), name='exchange_detail'),
    path('exchange/<int:exchange_id>/update_exchange/', views.update_exchange, name='update_exchange'),
    path('market/<int:pk>/', views.MarketDetailView.as_view(), name='market_detail'),
    path('traders/', views.TraderListView.as_view(), name='trader_list'),
    path('trader/<int:pk>/', views.TraderDetailView.as_view(), name='trader_detail'),
    path('trader/<int:trader_id>/create_order/', views.create_order, name='create_order'),
    path('order/<int:order_id>/edit_order/', views.edit_order, name='edit_order'),
]