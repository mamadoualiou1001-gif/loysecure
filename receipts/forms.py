from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Receipt
from datetime import datetime

class ReceiptForm(forms.ModelForm):
    """
    Formulaire pour certifier une quittance
    """
    class Meta:
        model = Receipt
        fields = ('month', 'amount', 'payment_method')
        widgets = {
            'month': forms.DateInput(
                attrs={'class': 'form-control', 'placeholder': 'JJ/MM/AAAA'},
                format='%d/%m/%Y'
            ),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si une instance existe, formater la date pour l'affichage
        if self.instance and self.instance.month:
            self.initial['month'] = self.instance.month.strftime('%d/%m/%Y')
    
    def clean_month(self):
        month = self.cleaned_data.get('month')
        from datetime import date
        
        # Si month est une string, la convertir
        if isinstance(month, str):
            try:
                month = datetime.strptime(month, '%d/%m/%Y').date()
            except ValueError:
                raise forms.ValidationError(_('Format de date invalide. Utilisez JJ/MM/AAAA (ex: 02/05/2026)'))
        
        if month and month > date.today():
            raise forms.ValidationError(_('Le mois ne peut pas être dans le futur.'))
        return month