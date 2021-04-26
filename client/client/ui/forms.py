from django import forms

class RegisterForm(forms.Form):
    user_name   = forms.CharField(required=True, label='UserName', max_length=100)
    password    = forms.CharField(required=True, label='Password',  max_length=100, widget=forms.PasswordInput())
    bank_name   = forms.CharField(required=True, label='Blood Bank Name', max_length=100)
    location    = forms.CharField(required=True, label='Location', max_length=100)

class LoginForm(forms.Form):
    user_name = forms.CharField(required=True, label='UserName', max_length=100)
    password = forms.CharField(required=True, label='Password',  max_length=100, widget=forms.PasswordInput())

class UploadFileForm(forms.Form):
    file = forms.FileField()
    password = forms.CharField(required=True, label='Password',  max_length=100, widget=forms.PasswordInput())

class FindDonorForm(forms.Form):
    BLOOD_CHOICES = (
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("O+", "O+"),
        ("O-", "O-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("BOMBAY", "Bombay"),
        ("H+", "H+"),
    )
    blood_group = forms.ChoiceField(required=True, label='Blood Group', choices=BLOOD_CHOICES)
    city = forms.CharField(required=True, label='City', max_length=100)