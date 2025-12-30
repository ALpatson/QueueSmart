from django import forms
from .models import CustomUser, Service

class RegistrationForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('client', 'Client'), ('staff', 'Staff'), ('admin', 'Admin')])


class BookingForm(forms.Form):
    service = forms.ModelChoiceField(
        queryset=Service.objects.all(),
        label="Select Service"
    )
    appointment_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    appointment_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time'})
    )
    notes = forms.CharField(
        widget=forms.Textarea,
        required=False,
        label="Additional Notes"
    )