from django import forms
from .models import Event, Organization

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'datetime', 'seats', 'image']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', "address"]