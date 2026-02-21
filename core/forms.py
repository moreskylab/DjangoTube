from django import forms
from django.contrib.auth.models import User
from .models import Video, Comment

class VideoUploadForm(forms.ModelForm):
    video_file = forms.FileField(label="Select Video")
    thumbnail_file = forms.ImageField(label="Select Thumbnail")

    class Meta:
        model = Video
        fields = ['title', 'description']

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a comment...', 'class': 'form-control'})
        }

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    class Meta:
        model = User
        fields = ['username', 'email', 'password']