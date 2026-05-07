from django.contrib import admin
from .models import Receipt

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'month', 'amount', 'status', 'certified_at')
    list_filter = ('status', 'payment_method', 'certified_at')
    search_fields = ('tenant__name', 'tenant__property__address')