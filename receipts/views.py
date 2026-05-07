from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import FileResponse
from datetime import datetime
from django.core.files.base import ContentFile
from tenants.models import Tenant
from subscriptions.services import LoySecureService
from .models import Receipt
from .forms import ReceiptForm
from .pdf_generator import ReceiptPDFGenerator

service = LoySecureService()

@login_required
def receipt_list(request):
    """Liste des quittances"""
    receipts = Receipt.objects.filter(owner=request.user).order_by('-month')
    return render(request, 'receipts/list.html', {'receipts': receipts})

@login_required
def receipt_create(request, tenant_id):
    """Créer ou mettre à jour une quittance"""
    tenant = get_object_or_404(Tenant, pk=tenant_id, property_ref__owner=request.user)
    
    # Vérifier si le propriétaire peut certifier
    can_certify, reason, deduction_type = request.user.can_certify()
    if not can_certify:
        messages.error(request, reason)
        return redirect('subscriptions:dashboard')
    
    if request.method == 'POST':
        form = ReceiptForm(request.POST)
        if form.is_valid():
            month_date = form.cleaned_data['month']
            rooms = tenant.property_ref.number_of_rooms
            
            # Vérifier si une quittance existe déjà pour ce mois
            existing_receipt = Receipt.objects.filter(tenant=tenant, month=month_date).first()
            
            if existing_receipt:
                # MODE MISE À JOUR : On met à jour la quittance existante
                receipt = existing_receipt
                
                # Mettre à jour les champs modifiables
                receipt.payment_method = form.cleaned_data['payment_method']
                receipt.amount = form.cleaned_data['amount']
                receipt.updated_at = timezone.now()
                
                # Ne pas recertifier, garder le statut et la date originales
                # Mais régénérer le PDF avec les nouvelles infos
                receipt.save()
                
                # Régénérer le PDF avec les nouvelles données
                pdf_gen = ReceiptPDFGenerator(receipt)
                pdf_buffer = pdf_gen.generate()
                receipt.pdf_file.save(f"quittance_{receipt.id}.pdf", ContentFile(pdf_buffer.getvalue()))
                
                messages.success(request, _('✅ Quittance mise à jour avec succès !'))
                return redirect('receipts:list')
            else:
                # MODE CRÉATION : On crée une nouvelle quittance
                result = service.process_certification(request.user, rooms)
                
                if not result['success']:
                    messages.error(request, result['message'])
                    return redirect('subscriptions:dashboard')
                
                receipt = form.save(commit=False)
                receipt.owner = request.user
                receipt.tenant = tenant
                receipt.certified_at = timezone.now()
                receipt.status = 'certified'
                receipt.cost_in_credits = rooms if result['credits_used'] else 0
                receipt.was_free = result['was_free']
                receipt.free_reason = result.get('free_reason', '')
                receipt.save()
                
                # Générer le PDF
                pdf_gen = ReceiptPDFGenerator(receipt)
                pdf_buffer = pdf_gen.generate()
                receipt.pdf_file.save(f"quittance_{receipt.id}.pdf", ContentFile(pdf_buffer.getvalue()))
                
                # Message de confirmation selon le type d'offre
                if result['was_free']:
                    if result['free_reason'] == 'premier_mois':
                        messages.success(request, _('✅ Quittance certifiée ! (Premier mois gratuit - offre de bienvenue)'))
                    elif result['free_reason'] == 'mois_offert':
                        messages.success(request, _('✅ Quittance certifiée ! (Mois offert après 5 mois payés)'))
                    else:
                        messages.success(request, _('✅ Quittance certifiée gratuitement !'))
                else:
                    messages.success(request, _('✅ Quittance certifiée !'))
                
                return redirect('receipts:list')
    else:
        # GET : Pré-remplir le formulaire avec une quittance existante si disponible
        current_month = datetime.now().replace(day=1).date()
        existing_receipt = Receipt.objects.filter(tenant=tenant, month=current_month).first()
        
        if existing_receipt:
            initial = {
                'month': existing_receipt.month,
                'amount': existing_receipt.amount,
                'payment_method': existing_receipt.payment_method,
            }
        else:
            initial = {
                'month': current_month,
                'amount': tenant.rent_amount,
            }
        form = ReceiptForm(initial=initial)
    
    return render(request, 'receipts/form.html', {
        'form': form,
        'tenant': tenant,
        'title': _('Certifier un paiement')
    })

@login_required
def receipt_download(request, pk):
    """Télécharger une quittance"""
    receipt = get_object_or_404(Receipt, pk=pk, owner=request.user)
    
    if receipt.pdf_file:
        return FileResponse(
            receipt.pdf_file.open(),
            as_attachment=True,
            filename=f"quittance_{receipt.month.strftime('%Y_%m')}.pdf"
        )
    else:
        messages.error(request, _('PDF non disponible.'))
        return redirect('receipts:list')