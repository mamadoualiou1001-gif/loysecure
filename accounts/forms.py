from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class UserRegistrationForm(UserCreationForm):
    """
    Formulaire d'inscription
    """
    phone = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '77 123 45 67'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Nettoyer le numéro
        phone = ''.join(filter(str.isdigit, phone))
        if len(phone) < 9:
            raise forms.ValidationError(_('Le numéro de téléphone doit contenir au moins 9 chiffres.'))
        return phone

class UserProfileForm(forms.ModelForm):
    """
    Formulaire de modification de profil
    """
    class Meta:
        model = CustomUser
        fields = ('phone', 'currency', 'company_name', 'address')
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }