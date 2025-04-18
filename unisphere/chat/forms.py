from django import forms
from django.contrib.auth.models import User
from .models import Profile

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'relationship_status', 'year', 'branch', 'bio', 'profile_pic']

class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'relationship_status', 'year', 'branch', 'bio', 'profile_pic']