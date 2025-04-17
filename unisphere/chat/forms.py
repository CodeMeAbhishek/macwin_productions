from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Profile

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    full_name = forms.CharField(max_length=100)
    branch = forms.CharField(max_length=50, required=False)
    year = forms.CharField(max_length=10, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    profile_pic = forms.ImageField(required=False)
    relationship_status = forms.ChoiceField(
        choices=Profile.RELATIONSHIP_CHOICES, required=False
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password',
                  'full_name', 'branch', 'year', 'bio', 'profile_pic', 'relationship_status']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.endswith('@nuv.ac.in'):
            raise forms.ValidationError("Only @nu.ac.in emails allowed.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        cpw = cleaned_data.get('confirm_password')
        if pw != cpw:
            raise forms.ValidationError("Passwords do not match.")

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'branch', 'year', 'bio', 'profile_pic', 'relationship_status']