from django import forms

class RegisterForm(forms.Form):
    user_name = forms.CharField(required=True, label='UserName', max_length=100)
    password = forms.CharField(required=True, label='Password',  max_length=100, widget=forms.PasswordInput())
