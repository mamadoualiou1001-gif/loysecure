from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from .forms import UserRegistrationForm, UserProfileForm

def register(request):
    """Inscription d'un nouveau propriétaire"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.subscription_type = 'free_trial'
            user.credits_balance = 10  # 10 quittances offertes pour l'essai
            user.save()
            login(request, user)
            messages.success(request, _('Bienvenue sur LoySecure ! Votre premier mois est gratuit.'))
            return redirect('properties:declare_rooms')
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    """Page de profil du propriétaire"""
    return render(request, 'accounts/profile.html')

@login_required
def edit_profile(request):
    """Modification du profil"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profil mis à jour.'))
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})