from django import forms

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