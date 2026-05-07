import uuid
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _
from .models import Payment

class LoySecureService:
    """
    Service de gestion hybride (abonnement + pay-per-use)
    """
    
    def get_credits_packs(self):
        """Liste des packs de crédits disponibles"""
        return [
            {'credits': 30, 'price': 2500, 'display': '30 crédits - 2 500 FCFA'},
            {'credits': 70, 'price': 5000, 'display': '70 crédits - 5 000 FCFA'},
            {'credits': 150, 'price': 10000, 'display': '150 crédits - 10 000 FCFA'},
        ]
    
    def get_credits_pack_price(self, credits):
        """Retourne le prix d'un pack de crédits"""
        if credits == 30:
            return 2500
        elif credits == 70:
            return 5000
        elif credits == 150:
            return 10000
        return credits * 100
    
    def process_certification(self, user, rooms_count):
        """
        Traite la certification d'une quittance
        Retourne un dictionnaire avec success, message, credits_used, was_free, free_reason
        """
        # Vérifier d'abord les prérequis
        if user.properties.count() == 0:
            return {'success': False, 'message': _('Déclarez vos logements')}
        
        if rooms_count == 0:
            return {'success': False, 'message': _('Chambres non déclarées')}
        
        # Abonnement
        if user.subscription_type == 'subscription':
            if not user.subscription_active:
                return {'success': False, 'message': _('Abonnement inactif')}
            if user.subscription_end_date and user.subscription_end_date < timezone.now():
                return {'success': False, 'message': _('Abonnement expiré')}
            
            # Vérifier si le mois est gratuit
            is_free, free_reason = user.is_month_free()
            if is_free:
                if free_reason == "premier_mois":
                    user.mark_first_month_free_used()
                    return {
                        'success': True, 
                        'message': _('Premier mois gratuit'), 
                        'credits_used': 0, 
                        'was_free': True,
                        'free_reason': 'premier_mois'
                    }
                elif free_reason == "mois_offert":
                    user.use_free_month_offer()
                    return {
                        'success': True, 
                        'message': _('Mois offert après 5 mois payés'), 
                        'credits_used': 0, 
                        'was_free': True,
                        'free_reason': 'mois_offert'
                    }
            
            return {
                'success': True, 
                'message': _('Abonnement actif'), 
                'credits_used': 0, 
                'was_free': False,
                'free_reason': ''
            }
        
        # Pay-per-use
        elif user.subscription_type == 'pay_per_use':
            if user.credits_balance < rooms_count:
                return {
                    'success': False, 
                    'message': _('Crédits insuffisants. Besoin de {need} crédits. Solde: {balance}').format(
                        need=rooms_count, balance=user.credits_balance
                    )
                }
            
            user.credits_balance -= rooms_count
            user.save()
            return {
                'success': True, 
                'message': _('Pay-per-use'), 
                'credits_used': rooms_count, 
                'was_free': False,
                'free_reason': ''
            }
        
        # Essai gratuit (pay-per-use)
        elif user.subscription_type == 'free_trial':
            if user.free_trial_usage >= 10:
                return {
                    'success': False, 
                    'message': _('Période d\'essai terminée. Choisissez une offre.')
                }
            
            user.free_trial_usage += 1
            user.save()
            remaining = 10 - user.free_trial_usage
            return {
                'success': True, 
                'message': _('Période d\'essai ({remaining}/10 utilisations restantes)').format(remaining=remaining),
                'credits_used': 0, 
                'was_free': True,
                'free_reason': 'free_trial'
            }
        
        return {'success': False, 'message': _('Erreur inattendue')}
    
    def simulate_payment(self, user, payment_type, amount):
        """Simuler un paiement d'abonnement (développement)"""
        try:
            payment = Payment.objects.create(
                owner=user,
                payment_type=payment_type,
                amount=amount,
                currency=user.currency,
                payment_method='simulation',
                status='success',
                transaction_id=str(uuid.uuid4())[:8],
            )
            
            if payment_type == 'subscription':
                self._activate_subscription(user)
                self._record_paid_month(user, amount, 'simulation')
            
            return {'success': True, 'payment_id': str(payment.id)}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def simulate_credits_purchase(self, user, credits):
        """Simuler l'achat de crédits (développement)"""
        try:
            price = self.get_credits_pack_price(credits)
            payment = Payment.objects.create(
                owner=user,
                payment_type='credits',
                amount=price,
                currency=user.currency,
                payment_method='simulation',
                status='success',
                credits_purchased=credits,
                transaction_id=str(uuid.uuid4())[:8],
            )
            
            user.credits_balance += credits
            user.save()
            
            return {
                'success': True, 
                'message': _('{credits} crédits ajoutés. Nouveau solde : {balance}').format(
                    credits=credits, balance=user.credits_balance
                )
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _activate_subscription(self, user):
        """Activer l'abonnement d'un propriétaire"""
        user.subscription_type = 'subscription'
        user.subscription_active = True
        user.subscription_tier = user.get_subscription_tier_name()
        if not user.subscription_start_date:
            user.subscription_start_date = timezone.now()
        user.subscription_end_date = timezone.now() + timedelta(days=30)
        user.save()
    
    def _record_paid_month(self, user, amount, method):
        """Enregistre un mois payé pour le compteur de l'offre"""
        # Vérifier si c'est un mois gratuit (premier mois)
        is_free, _ = user.is_month_free()
        
        if not is_free and user.subscription_type == 'subscription':
            user.record_paid_month()
    
    def get_subscription_status(self, user):
        """Retourne le statut détaillé de l'abonnement"""
        if user.subscription_type != 'subscription':
            return None
        
        is_free, free_reason = user.is_month_free()
        
        # Calculer le prochain mois offert
        next_free_month = None
        if not user.first_year_complete and not user.free_month_used and user.subscription_type == 'subscription':
            months_needed = 5 - user.consecutive_paid_months
            if months_needed > 0 and months_needed < 5:
                next_free_month = months_needed
        
        # Date de fin de la 1ère année
        first_year_end_date = None
        if user.subscription_start_date:
            first_year_end_date = user.subscription_start_date + timedelta(days=365)
        
        return {
            'is_free': is_free,
            'free_reason': free_reason,
            'consecutive_paid_months': user.consecutive_paid_months,
            'free_month_used': user.free_month_used,
            'first_year_complete': user.first_year_complete,
            'first_year_end_date': first_year_end_date,
            'next_free_month_in': next_free_month,
            'subscription_end_date': user.subscription_end_date,
            'subscription_active': user.subscription_active,
            'current_price': user.get_subscription_price(),
        }