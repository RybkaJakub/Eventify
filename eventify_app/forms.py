from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Button
from django import forms
from .models import Event, Organization

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'datetime', 'seats', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zadej název eventu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Zadej popisek eventu'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10000}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
        labels = {
            'name': 'Název Eventu',
            'description': 'Popisek Eventu',
            'seats': 'Počet sedadel',
            'image': 'Foto Eventu',
            'datetime': 'Datum konání Eventu'
        }

    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-md-3'
        self.helper.field_class = 'col-md-9'
        self.helper.layout = Layout(
            Fieldset(
                'Informace o eventu',
                'name',
                'description',
                'seats',
                'image',
                'datetime',
            ),
            ButtonHolder(
                Submit('submit', 'Uložit', css_class='btn-primary mr-2'),
                Button('cancel', 'Storno', css_class='btn-secondary', onclick='window.history.back();')
            )
        )
class OrganisationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', "address"]