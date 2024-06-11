from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Button
from django import forms
from .models import Event, Organization
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.dateformat import format

CustomUser = get_user_model()

from django import forms
from .models import Event
from .models import Organization


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'day', 'start_time', 'end_time', 'seats', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zadej název eventu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Zadej popisek eventu'}),
            'day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10000}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Název Eventu',
            'description': 'Popisek Eventu',
            'day': 'Datum konání Eventu',
            'start_time': 'Čas začátku eventu',
            'end_time': 'Čas konce eventu',
            'seats': 'Počet sedadel',
            'image': 'Foto Eventu',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
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
                'day',
                'start_time',
                'end_time',
                'seats',
                'image',
            ),
            ButtonHolder(
                Submit('submit', 'Uložit', css_class='btn-primary mr-2'),
                Button('cancel', 'Storno', css_class='btn-secondary', onclick='window.history.back();')
            )
        )

class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'seats', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zadej název eventu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Zadej popisek eventu'}),
            'seats': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10000}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Název Eventu',
            'description': 'Popisek Eventu',
            'seats': 'Počet sedadel',
            'image': 'Foto Eventu',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
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
            ),
            ButtonHolder(
                Submit('submit', 'Uložit', css_class='btn-primary mr-2'),
                Button('cancel', 'Storno', css_class='btn-secondary', onclick='window.history.back();')
            )
        )


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', "address"]

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super(CustomAuthenticationForm, self).__init__(*args, **kwargs)
        ButtonHolder(
            Submit('submit', 'Přihlásit se', css_class='btn-primary mr-2')
        )

class LogoutForm(forms.Form):
    pass

class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'telephone', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'first_name',
            'last_name',
            'username',
            'telephone',
            'email',
            'password1',
            'password2',
            Submit('submit', 'Sign Up', css_class='btn-success')
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2