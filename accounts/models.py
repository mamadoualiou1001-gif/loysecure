from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

class CustomUser(AbstractUser):
    """
    Modèle utilisateur LOYSECURE
    """
    CURRENCY_CHOICES = [
        ('XOF', 'Franc CFA (XOF) - Sénégal, Côte d\'Ivoire, Bénin, Togo, Burkina, Mali, Niger'),
        ('XAF', 'Franc CFA (XAF) - Cameroun, Gabon, Congo, RCA, Tchad'),
        ('GNF', 'Franc Guinéen (GNF) - Guinée'),
    ]
    
    SUBSCRIPTION_TYPE_CHOICES = [
        ('free_trial', _('Essai gratuit (1er mois)')),
        ('pay_per_use', _('Pay-per-use (100 FCFA/chambre)')),
        ('subscription', _('Abonnement mensuel')),
    ]
    
    # Informations personnelles
    phone = models.CharField(_('Téléphone'), max_length=20, unique=True)
    currency = models.CharField(_('Devise'), max_length=3, choices=CURRENCY_CHOICES, default='XOF')
    company_name = models.CharField(_('Entreprise'), max_length=200, blank=True)
    address = models.TextField(_('Adresse'), blank=True)
    
    # Type d'abonnement
    subscription_type = models.CharField(
        _('Type d\'abonnement'), 
        max_length=20, 
        choices=SUBSCRIPTION_TYPE_CHOICES, 
        default='free_trial'
    )
    
    # Pay-per-use
    credits_balance = models.IntegerField(_('Crédits disponibles'), default=0)
    
    # Abonnement
    subscription_active = models.BooleanField(_('Abonnement actif'), default=False)
    subscription_start_date = models.DateTimeField(_('Début abonnement'), null=True, blank=True)
    subscription_end_date = models.DateTimeField(_('Fin abonnement'), null=True, blank=True)
    subscription_tier = models.CharField(_('Tranche abonnement'), max_length=20, blank=True)
    
    # Suivi de l'offre (1er mois gratuit + 5 payés → 1 offert, uniquement 1ère année)
    first_month_free_used = models.BooleanField(_('1er mois gratuit utilisé'), default=False)
    consecutive_paid_months = models.IntegerField(_('Mois payés consécutifs'), default=0)
    free_month_used = models.BooleanField(_('Mois offert utilisé'), default=False)
    first_year_complete = models.BooleanField(_('1ère année terminée'), default=False)
    
    # Pour le pay-per-use (essai)
    free_trial_usage = models.IntegerField(_('Quittances utilisées pendant essai'), default=0)
    
    # Déclaration des chambres (antifraude)
    total_rooms_declared = models.IntegerField(_('Total chambres déclarées'), default=0)
    last_compliance_check = models.DateTimeField(_('Dernier contrôle conformité'), null=True, blank=True)
    
    # Dates
    created_at = models.DateTimeField(_('Date d\'inscription'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Date de mise à jour'), auto_now=True)
    
    class Meta:
        verbose_name = _('Propriétaire')
        verbose_name_plural = _('Propriétaires')
    
    def __str__(self):
        return f"{self.username} ({self.phone})"
    
    def get_total_rooms(self):
        """Calcule le nombre total de chambres déclarées"""
        total = sum(p.number_of_rooms for p in self.properties.all())
        if self.total_rooms_declared != total:
            self.total_rooms_declared = total
            self.save(update_fields=['total_rooms_declared'])
        return total
    
    def get_subscription_price(self):
        """Retourne le prix mensuel selon le nombre de chambres"""
        rooms = self.get_total_rooms()
        if rooms <= 10:
            return 1000
        elif rooms <= 20:
            return 1500
        else:
            return 2000
    
    def get_subscription_tier_name(self):
        """Retourne le nom de la tranche d'abonnement"""
        rooms = self.get_total_rooms()
        if rooms <= 10:
            return 'small'
        elif rooms <= 20:
            return 'medium'
        return 'large'
    
    def get_tier_display_name(self):
        """Retourne l'affichage de la tranche"""
        tiers = {
            'small': _('Petit propriétaire (≤ 10 chambres)'),
            'medium': _('Propriétaire moyen (11-20 chambres)'),
            'large': _('Grand propriétaire (21+ chambres)'),
        }
        return tiers.get(self.get_subscription_tier_name(), '')
    
    def get_currency_symbol(self):
        """Retourne le symbole de la devise"""
        symbols = {'XOF': 'FCFA', 'XAF': 'FCFA', 'GNF': 'GNF'}
        return symbols.get(self.currency, 'FCFA')
    
    def get_recommended_offer(self):
        """Recommande la meilleure offre pour le propriétaire"""
        rooms = self.get_total_rooms()
        if rooms == 0:
            return {
                'type': None, 
                'price': 0, 
                'message': _('Ajoutez vos logements pour voir l\'offre recommandée')
            }
        
        pay_cost = rooms * 100
        if rooms <= 10:
            sub_cost = 1000
        elif rooms <= 20:
            sub_cost = 1500
        else:
            sub_cost = 2000
        
        if pay_cost <= sub_cost:
            return {
                'type': 'pay_per_use', 
                'price': pay_cost, 
                'message': _('Pay-per-use : {price} FCFA/mois').format(price=pay_cost)
            }
        else:
            return {
                'type': 'subscription', 
                'price': sub_cost, 
                'message': _('Abonnement : {price} FCFA/mois').format(price=sub_cost)
            }
    
    def is_month_free(self):
        """
        Détermine si le mois en cours est gratuit
        Retourne (bool, raison)
        """
        # Règle 1 : 1er mois gratuit (offre de bienvenue) - UNIQUEMENT pour abonnement
        if not self.first_month_free_used and self.subscription_type == 'subscription':
            return True, "premier_mois"
        
        # Règle 2 : Vérifier si on est dans la 1ère année
        if self.subscription_start_date and not self.first_year_complete:
            days_since_start = (timezone.now() - self.subscription_start_date).days
            if days_since_start > 365:
                self.first_year_complete = True
                self.save(update_fields=['first_year_complete'])
        
        # Règle 3 : Si 1ère année et mois offert non utilisé
        if not self.first_year_complete and not self.free_month_used and self.subscription_type == 'subscription':
            if self.consecutive_paid_months >= 5:
                return True, "mois_offert"
        
        return False, None
    
    def use_free_month_offer(self):
        """Consomme le mois offert (après 5 mois payés)"""
        if not self.first_year_complete and not self.free_month_used and self.consecutive_paid_months >= 5:
            self.free_month_used = True
            self.consecutive_paid_months = 0
            self.save(update_fields=['free_month_used', 'consecutive_paid_months'])
            return True
        return False
    
    def mark_first_month_free_used(self):
        """Marque le premier mois gratuit comme utilisé"""
        if not self.first_month_free_used:
            self.first_month_free_used = True
            if not self.subscription_start_date:
                self.subscription_start_date = timezone.now()
            self.save(update_fields=['first_month_free_used', 'subscription_start_date'])
            return True
        return False
    
    def can_certify(self):
        """
        Vérifie si le propriétaire peut certifier une quittance
        Retourne (allowed, reason, deduction_type)
        """
        rooms = self.get_total_rooms()
        
        # Vérifications préalables
        if self.properties.count() == 0:
            return False, _('Veuillez d\'abord déclarer vos logements.'), None
        if rooms == 0:
            return False, _('Veuillez déclarer le nombre de chambres pour chaque logement.'), None
        
        # Abonnement
        if self.subscription_type == 'subscription':
            if not self.subscription_active:
                return False, _('Votre abonnement est inactif. Veuillez le réactiver.'), None
            if self.subscription_end_date and self.subscription_end_date < timezone.now():
                return False, _('Votre abonnement a expiré. Veuillez renouveler.'), None
            
            # Vérifier si le mois est gratuit
            is_free, free_reason = self.is_month_free()
            if is_free:
                if free_reason == "premier_mois":
                    return True, _('Premier mois gratuit (offre de bienvenue)'), 'free_first_month'
                elif free_reason == "mois_offert":
                    return True, _('Mois offert (après 5 mois payés consécutifs)'), 'free_offer_month'
            
            return True, _('Abonnement actif'), 'subscription'
        
        # Pay-per-use
        elif self.subscription_type == 'pay_per_use':
            if self.credits_balance < rooms:
                return False, _('Crédits insuffisants. Besoin de {rooms} crédits.').format(rooms=rooms), None
            return True, _('Pay-per-use'), 'credits'
        
        # Essai gratuit (1er mois pour pay-per-use)
        elif self.subscription_type == 'free_trial':
            if self.free_trial_usage >= 10:
                return False, _('Votre période d\'essai est terminée. Veuillez choisir une offre.'), None
            return True, _('Période d\'essai gratuite. Quittance {used}/10.').format(used=self.free_trial_usage + 1), 'free_trial'
        
        return False, _('Erreur inattendue'), None
    
    def record_paid_month(self):
        """Enregistre un mois payé pour le compteur de l'offre"""
        if self.subscription_type == 'subscription' and not self.first_year_complete and not self.free_month_used:
            self.consecutive_paid_months += 1
            self.save(update_fields=['consecutive_paid_months'])
            return True
        return False