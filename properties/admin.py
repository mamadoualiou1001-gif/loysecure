from django.contrib import admin
from .models import Property

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('address', 'owner', 'number_of_rooms', 'created_at')
    list_filter = ('owner', 'is_active')
    search_fields = ('address', 'owner__username')