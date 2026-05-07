from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.utils.translation import gettext_lazy as _
from .models import Property
from .forms import PropertyForm, PropertyFormSet

@login_required
def dashboard(request):
    """Tableau de bord principal du propriétaire"""
    properties = request.user.properties.all()
    total_rooms = request.user.get_total_rooms()
    total_tenants = sum(p.tenants.count() for p in properties)
    active_tenants = sum(p.tenants.filter(is_active=True).count() for p in properties)
    total_monthly_rent = sum(p.get_total_rent_per_month() for p in properties)
    
    context = {
        'properties': properties,
        'total_rooms': total_rooms,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'total_monthly_rent': total_monthly_rent,
        'subscription_active': request.user.subscription_active,
        'subscription_end_date': request.user.subscription_end_date,
        'credits_balance': request.user.credits_balance,
        'subscription_type': request.user.subscription_type,
    }
    return render(request, 'properties/dashboard.html', context)

@login_required
def declare_rooms(request):
    """Déclaration des logements et chambres (obligatoire)"""
    PropertyFormSetFactory = formset_factory(PropertyForm, formset=PropertyFormSet, extra=1, can_delete=True)
    
    if request.method == 'POST':
        formset = PropertyFormSetFactory(request.POST)
        if formset.is_valid():
            # Supprimer les anciennes propriétés
            request.user.properties.all().delete()
            
            # Créer les nouvelles
            total_rooms = 0
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    prop = form.save(commit=False)
                    prop.owner = request.user
                    prop.save()
                    total_rooms += prop.number_of_rooms
            
            # Mettre à jour le total
            request.user.total_rooms_declared = total_rooms
            request.user.save()
            
            messages.success(request, _('Vos logements ont été enregistrés avec succès.'))
            
            # Rediriger vers l'abonnement ou le dashboard
            if request.user.subscription_type == 'free_trial':
                return redirect('subscriptions:dashboard')
            return redirect('properties:dashboard')
        else:
            messages.error(request, _('Veuillez corriger les erreurs ci-dessous.'))
    else:
        initial_data = []
        for prop in request.user.properties.all():
            initial_data.append({
                'address': prop.address,
                'number_of_rooms': prop.number_of_rooms,
                'description': prop.description,
            })
        formset = PropertyFormSetFactory(initial=initial_data)
    
    return render(request, 'properties/declare_rooms.html', {'formset': formset})