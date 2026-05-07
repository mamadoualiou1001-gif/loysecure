from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Property(models.Model):
    """
    Modèle pour les logements d'un propriétaire
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties',
        verbose_name=_('Propriétaire')
    )
    address = models.CharField(_('Adresse'), max_length=500)
    number_of_rooms = models.PositiveIntegerField(_('Nombre de chambres'), default=1)
    description = models.TextField(_('Description'), blank=True)
    is_active = models.BooleanField(_('Actif'), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Logement')
        verbose_name_plural = _('Logements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.address} ({self.number_of_rooms} chambres)"
    
    def get_active_tenants_count(self):
        """Nombre de locataires actifs dans ce logement"""
        return self.tenants.filter(is_active=True).count()
    
    def get_total_rent_per_month(self):
        """Revenu locatif total mensuel"""
        return sum(t.rent_amount for t in self.tenants.filter(is_active=True))