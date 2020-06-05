import json

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from app.models import Destination
from users.models import User


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
        exclude = 'id', 'owner', 'config_type', 'config_id', 'shared',


class ConfigForm(ModelForm):
    def clean_saved_config(self):
        data = self.cleaned_data['saved_config']
        try:
            json.loads(data)
        except json.JSONDecodeError:
            raise ValidationError('Invalid JSON provided')
        return data

    class Meta:
        model = User
        fields = 'saved_config',


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput())
    new_password1 = forms.CharField(widget=forms.PasswordInput())
    new_password2 = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        if not self.user.check_password(self.cleaned_data['old_password']):
            raise forms.ValidationError('Invalid old password')
        return self.cleaned_data['old_password']

    def clean(self):
        if self.cleaned_data['new_password1'] != self.cleaned_data['new_password2']:
            raise forms.ValidationError('Passwords do not match')
        return self.cleaned_data
