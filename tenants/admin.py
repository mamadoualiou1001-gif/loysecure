from django.contrib import admin
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('id', 'property_ref', 'name', 'phone', 'rent_amount', 'is_active')  # Changé: property -> property_ref
    list_filter = ('is_active', 'property_ref__owner')  # Changé: property__owner -> property_ref__owner
    search_fields = ('name', 'phone', 'email', 'property_ref__address')  # Changé: property__address -> property_ref__address
    list_editable = ('rent_amount', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('name', 'phone', 'email')
        }),
        ('Informations du logement', {
            'fields': ('property_ref', 'rent_amount')  # Changé: property -> property_ref
        }),
        ('Contrat', {
            'fields': ('contract_start_date', 'contract_end_date', 'is_active')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )