from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'subscription_type', 'subscription_active', 'total_rooms_declared', 'created_at')
    list_filter = ('subscription_type', 'subscription_active', 'first_year_complete', 'currency')
    search_fields = ('username', 'email', 'phone')
    
    fieldsets = UserAdmin.fieldsets + (
        (_('Informations LoySecure'), {
            'fields': ('phone', 'currency', 'company_name', 'address')
        }),
        (_('Abonnement'), {
            'fields': ('subscription_type', 'credits_balance', 'subscription_active', 
                      'subscription_start_date', 'subscription_end_date', 'subscription_tier')
        }),
        (_('Offres et promotions'), {
            'fields': ('first_month_free_used', 'consecutive_paid_months', 'free_month_used', 'first_year_complete')
        }),
        (_('Déclaration'), {
            'fields': ('total_rooms_declared', 'last_compliance_check')
        }),
    )