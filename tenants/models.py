from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Tenant(models.Model):
    """
    Modèle pour les locataires
    """
    # Changement : renommer 'property' en 'property_ref' pour éviter la confusion
    property_ref = models.ForeignKey(
        'properties.Property',
        on_delete=models.CASCADE,
        related_name='tenants',
        verbose_name=_('Logement')
    )
    name = models.CharField(_('Nom complet'), max_length=200)
    phone = models.CharField(_('Numéro de téléphone'), max_length=20)
    email = models.EmailField(_('Email'), blank=True)
    rent_amount = models.PositiveIntegerField(_('Montant du loyer'))
    contract_start_date = models.DateField(_('Début du contrat'), null=True, blank=True)
    contract_end_date = models.DateField(_('Fin du contrat'), null=True, blank=True)
    is_active = models.BooleanField(_('Actif'), default=True)
    notes = models.TextField(_('Notes'), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Locataire')
        verbose_name_plural = _('Locataires')
        ordering = ['name']
    
    def __str__(self):
        # Changement : utiliser property_ref au lieu de property
        return f"{self.name} - {self.property_ref.address}"
    
    @property
    def display_rent(self):
        # Changement : utiliser property_ref au lieu de property
        currency = self.property_ref.owner.get_currency_symbol()
        return f"{self.rent_amount:,} {currency}"