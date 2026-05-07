from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from .models import Tenant
from .forms import TenantForm
from properties.models import Property

@login_required
def tenant_list(request):
    """Liste des locataires"""
    tenants = Tenant.objects.filter(property_ref__owner=request.user)
    return render(request, 'tenants/list.html', {'tenants': tenants})

@login_required
def tenant_create(request):
    """Ajouter un locataire"""
    if not Property.objects.filter(owner=request.user).exists():
        messages.warning(request, 'Veuillez d\'abord ajouter un logement.')
        # MODIFIÉ : Redirection vers home au lieu de property_create (inexistant)
        return redirect('home')
    
    if request.method == 'POST':
        form = TenantForm(request.user, request.POST)
        if form.is_valid():
            tenant = form.save()
            messages.success(request, 'Locataire ajouté avec succès.')
            return redirect('tenants:tenant_list')
    else:
        form = TenantForm(request.user)
    
    return render(request, 'tenants/form.html', {'form': form, 'title': 'Ajouter un locataire'})

@login_required
def tenant_detail(request, pk):
    """Détail d'un locataire"""
    tenant = get_object_or_404(Tenant, pk=pk, property_ref__owner=request.user)
    return render(request, 'tenants/detail.html', {'tenant': tenant})

@login_required
def tenant_edit(request, pk):
    """Modifier un locataire"""
    tenant = get_object_or_404(Tenant, pk=pk, property_ref__owner=request.user)
    if request.method == 'POST':
        form = TenantForm(request.user, request.POST, instance=tenant)
        if form.is_valid():
            form.save()
            messages.success(request, 'Locataire modifié.')
            return redirect('tenants:tenant_list')
    else:
        form = TenantForm(request.user, instance=tenant)
    
    return render(request, 'tenants/form.html', {'form': form, 'title': 'Modifier le locataire'})

@login_required
def tenant_delete(request, pk):
    """Supprimer un locataire"""
    tenant = get_object_or_404(Tenant, pk=pk, property_ref__owner=request.user)
    if request.method == 'POST':
        tenant.delete()
        messages.success(request, 'Locataire supprimé.')
        return redirect('tenants:tenant_list')
    
    return render(request, 'tenants/confirm_delete.html', {'tenant': tenant})