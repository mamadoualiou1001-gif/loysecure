from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

class ComplianceMiddleware:
    """Middleware qui vérifie que le propriétaire a déclaré ses logements"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if request.user.is_authenticated:
            # URLs à exclure de la vérification
            excluded_urls = [
                reverse('accounts:logout'),
                reverse('accounts:profile'),
                reverse('accounts:edit_profile'),
                reverse('properties:declare_rooms'),
                reverse('subscriptions:dashboard'),
                reverse('home'),
                reverse('set_language'),
            ]
            
            current_path = request.path
            is_excluded = any(current_path == url or current_path.startswith(url) for url in excluded_urls)
            
            # Vérifier si le propriétaire a déclaré des logements
            if not is_excluded and not request.user.properties.exists():
                messages.warning(request, _('Veuillez d\'abord déclarer vos logements.'))
                return redirect('properties:declare_rooms')
        
        return self.get_response(request)