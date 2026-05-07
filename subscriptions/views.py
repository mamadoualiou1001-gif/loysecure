from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from .services import LoySecureService

service = LoySecureService()

@login_required
def subscription_dashboard(request):
    """Dashboard des abonnements avec suivi de l'offre"""
    user = request.user
    status = service.get_subscription_status(user)
    
    context = {
        'total_rooms': user.get_total_rooms(),
        'subscription_type': user.subscription_type,
        'subscription_active': user.subscription_active,
        'subscription_end_date': user.subscription_end_date,
        'subscription_tier': user.get_tier_display_name(),
        'subscription_price': user.get_subscription_price(),
        'credits_balance': user.credits_balance,
        'free_trial_used': user.free_trial_usage,
        'recommended': user.get_recommended_offer(),
        'credits_packs': service.get_credits_packs(),
        'subscription_status': status,
        'first_month_free_used': user.first_month_free_used,
        'first_year_complete': user.first_year_complete,
    }
    return render(request, 'subscriptions/dashboard.html', context)

@login_required
def subscribe(request):
    """Activer l'abonnement (premier mois gratuit)"""
    if request.method == 'POST':
        amount = request.user.get_subscription_price()
        result = service.simulate_payment(request.user, 'subscription', amount)
        if result['success']:
            messages.success(request, _('Abonnement activé ! Votre premier mois est gratuit.'))
            return redirect('subscriptions:dashboard')
        else:
            messages.error(request, result.get('message', _('Erreur lors de l\'activation.')))
    return redirect('subscriptions:dashboard')

@login_required
def buy_credits(request):
    """Acheter des crédits (pay-per-use)"""
    if request.method == 'POST':
        credits = int(request.POST.get('credits', 30))
        result = service.simulate_credits_purchase(request.user, credits)
        if result['success']:
            messages.success(request, result['message'])
        else:
            messages.error(request, result['message'])
    return redirect('subscriptions:dashboard')

@login_required
def switch_to_pay_per_use(request):
    """Passer au mode pay-per-use"""
    user = request.user
    user.subscription_type = 'pay_per_use'
    user.subscription_active = False
    user.save()
    messages.success(request, _('Mode pay-per-use activé.'))
    return redirect('subscriptions:dashboard')

@login_required
def switch_to_subscription(request):
    """Passer au mode abonnement"""
    user = request.user
    user.subscription_type = 'subscription'
    user.save()
    messages.info(request, _('Mode abonnement sélectionné. Activez-le en cliquant sur "S\'abonner".'))
    return redirect('subscriptions:dashboard')