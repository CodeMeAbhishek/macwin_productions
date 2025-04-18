from django import forms
from django.contrib.auth.models import User
from .models import Profile, Post, Comment

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

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What\'s on your mind?'
            }),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'placeholder': 'Write a comment...'}),
        }