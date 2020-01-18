from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import ModelForm

from app.models import Destination


class LoginForm(AuthenticationForm):
    remember = forms.BooleanField(required=False)


class SignupForm(forms.Form):
    username = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError('Passwords do not match')
        return self.cleaned_data


class DestinationForm(ModelForm):
    prefix = 'destination'

    class Meta:
        model = Destination
        exclude = 'id', 'owner', 'config_type', 'config_id',
