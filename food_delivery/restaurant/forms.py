from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError
import re


class SignUpForm(UserCreationForm):
    username = forms.CharField(
        label="Phone Number",
        max_length=10,
        min_length=10,
        required=True,
        help_text="Enter a 10-digit phone number.",
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter your phone number'})
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter your email'})
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter your first name'})
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter your last name'})
    )

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name',
                  'email', 'password1', 'password2']

    def clean_username(self):
        phone = self.cleaned_data.get('username')
        if not re.match(r'^\d{10}$', phone):
            raise ValidationError("Phone number must be exactly 10 digits.")
        return phone  # Duplicate check already handled in view


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_image', 'address']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.fields['username'].label = "Phone Number"
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your phone number',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
