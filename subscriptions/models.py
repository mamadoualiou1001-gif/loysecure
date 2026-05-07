from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid

class Payment(models.Model):
    """
    Modèle pour les paiements d'abonnement ou de crédits
    """
    PAYMENT_TYPE_CHOICES = [
        ('subscription', _('Abonnement mensuel')),
        ('credits', _('Achat de crédits')),
        ('free_month', _('Mois offert (promo)')),
        ('first_month_free', _('Premier mois gratuit (bienvenue)')),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('success', _('Réussi')),
        ('failed', _('Échoué')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('orange_money', _('Orange Money')),
        ('mtn_momo', _('MTN MoMo')),
        ('wave', _('Wave')),
        ('card', _('Carte bancaire')),
        ('simulation', _('Simulation (développement)')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('Propriétaire')
    )
    
    payment_type = models.CharField(_('Type de paiement'), max_length=30, choices=PAYMENT_TYPE_CHOICES)
    amount = models.PositiveIntegerField(_('Montant'))
    currency = models.CharField(_('Devise'), max_length=3, default='XOF')
    payment_method = models.CharField(_('Mode de paiement'), max_length=20, choices=PAYMENT_METHOD_CHOICES)
    
    status = models.CharField(_('Statut'), max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Pour l'achat de crédits
    credits_purchased = models.PositiveIntegerField(_('Crédits achetés'), default=0)
    
    # Pour le suivi de l'offre
    month_concerned = models.DateField(_('Mois concerné'), null=True, blank=True)
    
    # Transaction IDs
    transaction_id = models.CharField(_('ID transaction'), max_length=100, blank=True)
    api_response = models.JSONField(_('Réponse API'), default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Paiement')
        verbose_name_plural = _('Paiements')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_type} - {self.amount} {self.currency}"