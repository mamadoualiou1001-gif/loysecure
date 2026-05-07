from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('owner', 'payment_type', 'amount', 'status', 'created_at')
    list_filter = ('payment_type', 'status', 'payment_method')
    search_fields = ('owner__username', 'transaction_id')