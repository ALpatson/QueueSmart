from django import forms

class RegistrationForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('client', 'Client'), ('staff', 'Staff'), ('admin', 'Admin')])