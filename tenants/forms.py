from django import forms
from django.utils.translation import gettext_lazy as _
from properties.models import Property
from .models import Tenant

class TenantForm(forms.ModelForm):
    """
    Formulaire pour ajouter/modifier un locataire
    """
    class Meta:
        model = Tenant
        fields = ('property_ref', 'name', 'phone', 'email', 'rent_amount', 'contract_start_date', 'contract_end_date', 'notes')
        widgets = {
            'property_ref': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '77 123 45 67'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rent_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'contract_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['property_ref'].queryset = Property.objects.filter(owner=user)
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        phone = ''.join(filter(str.isdigit, phone))
        return phone