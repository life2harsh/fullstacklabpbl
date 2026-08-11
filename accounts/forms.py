from django import forms
from django.contrib.auth.models import User

from .models import Profile


class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone", "bio", "allow_mentions", "avatar"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 4})}


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]
