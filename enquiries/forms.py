from django import forms
from .models import Enquiry

class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['first_name', 'last_name', 'phone', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':'First Name'}),
            'last_name': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Last Name'}),
            'phone': forms.TextInput(attrs={'class':'form-control', 'placeholder':'Mobile'}),
            'email': forms.EmailInput(attrs={'class':'form-control', 'placeholder':'Email'}),
        }
