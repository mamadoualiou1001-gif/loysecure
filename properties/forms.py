from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Property

class PropertyForm(forms.ModelForm):
    """
    Formulaire pour ajouter/modifier un logement
    """
    class Meta:
        model = Property
        fields = ('address', 'number_of_rooms', 'description')
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': _('ex: Fann Hock, Dakar')
            }),
            'number_of_rooms': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 2, 
                'placeholder': _('Optionnel')
            }),
        }

class PropertyFormSet(forms.BaseFormSet):
    """
    FormSet pour la déclaration multiple
    """
    def clean(self):
        total_rooms = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                total_rooms += form.cleaned_data.get('number_of_rooms', 0)
        
        if total_rooms == 0:
            raise forms.ValidationError(_('Vous devez déclarer au moins une chambre.'))
        
        return total_rooms