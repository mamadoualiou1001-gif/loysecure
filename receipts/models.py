from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class Receipt(models.Model):
    """
    Modèle pour les quittances certifiées
    """
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('certified', _('Certifiée')),
        ('rejected', _('Rejetée')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash', _('Espèces')),
        ('orange_money', _('Orange Money')),
        ('mtn_momo', _('MTN MoMo')),
        ('wave', _('Wave')),
        ('bank_transfer', _('Virement bancaire')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name=_('Propriétaire')
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name=_('Locataire')
    )
    
    month = models.DateField(_('Mois concerné'))
    amount = models.PositiveIntegerField(_('Montant'))
    payment_method = models.CharField(_('Mode de paiement'), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    certified_at = models.DateTimeField(_('Date de certification'), null=True, blank=True)
    
    # Fichier PDF
    pdf_file = models.FileField(_('Fichier PDF'), upload_to='receipts/%Y/%m/', null=True, blank=True)
    
    # Envoi WhatsApp
    sent_to_tenant = models.BooleanField(_('Envoyé au locataire'), default=False)
    whatsapp_message_id = models.CharField(max_length=100, blank=True)
    
    # Coût pour le propriétaire
    cost_in_credits = models.PositiveIntegerField(_('Coût en crédits'), default=0)
    was_free = models.BooleanField(_('Était gratuit'), default=False)
    free_reason = models.CharField(_('Raison de la gratuité'), max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Quittance')
        verbose_name_plural = _('Quittances')
        ordering = ['-month']
        unique_together = ['tenant', 'month']
    
    def __str__(self):
        return f"Quittance {self.tenant.name} - {self.month.strftime('%B %Y')}"
    
    @property
    def month_display(self):
        return self.month.strftime('%B %Y')
    
    def save(self, *args, **kwargs):
        if not self.cost_in_credits and self.status == 'certified':
            rooms = self.tenant.property_ref.number_of_rooms
            self.cost_in_credits = rooms
        super().save(*args, **kwargs)