from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_dashboard, name='dashboard'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('buy-credits/', views.buy_credits, name='buy_credits'),
    path('switch/pay-per-use/', views.switch_to_pay_per_use, name='switch_to_pay_per_use'),
    path('switch/subscription/', views.switch_to_subscription, name='switch_to_subscription'),
]