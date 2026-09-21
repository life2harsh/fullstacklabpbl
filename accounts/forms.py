from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q

from .models import Profile


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Email or username", widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "you@example.com"}))

    def clean_username(self):
        identifier = self.cleaned_data["username"].strip()
        user = User.objects.filter(Q(email__iexact=identifier) | Q(username__iexact=identifier)).first()
        return user.username if user else identifier


class RegistrationForm(forms.Form):
    username = forms.RegexField(regex=r"^[A-Za-z0-9_]+$", max_length=50, error_messages={"invalid": "Use letters, numbers and underscores only."})
    email = forms.EmailField()
    full_name = forms.CharField(max_length=100, required=False)
    password = forms.CharField(widget=forms.PasswordInput)

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

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password"):
            try:
                validate_password(cleaned["password"], User(username=cleaned.get("username", ""), email=cleaned.get("email", "")))
            except forms.ValidationError as error:
                self.add_error("password", error)
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(username=data["username"], email=data["email"], password=data["password"])
        user.profile.full_name = data["full_name"]
        user.profile.save(update_fields=["full_name"])
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["full_name", "phone", "bio", "allow_mentions", "avatar"]
        widgets = {"bio": forms.Textarea(attrs={"rows": 3})}


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email"]
        help_texts = {"username": ""}

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Email already registered.")
        return email
