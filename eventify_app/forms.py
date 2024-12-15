from crispy_forms.bootstrap import FormActions
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Button
from django import forms
from .models import Event, Organization, DeliveryAddress, PaymentMethod, EventAddress
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model, login
from django.utils.dateformat import format

from django.shortcuts import redirect
CustomUser = get_user_model()

from django import forms
from .models import Event, Organization, TicketType, CustomUser
from django.contrib.auth import get_user_model
from django.forms import inlineformset_factory
from allauth.account.forms import SignupForm


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'day', 'time','image', 'category']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zadej název eventu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Zadej popisek eventu'}),
            'day': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Název Eventu',
            'description': 'Popisek Eventu',
            'day': 'Datum konání Eventu',
            'time': 'Čas konání Eventu',
            'image': 'Foto Eventu',
            'category': 'Kategorie Eventu',
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
                'time',
                'image',
                'category',
            ),
        )

class EventAddressForm(forms.ModelForm):
    class Meta:
        model = EventAddress
        fields = ['street', 'number', 'city', 'postal_code', 'country']
        widgets = {
            'street': forms.TextInput(attrs={'class': 'form-input'}),
            'number': forms.NumberInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class TicketTypeForm(forms.ModelForm):
    class Meta:
        model = TicketType
        fields = ['name', 'price', 'quantity']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'price': forms.NumberInput(attrs={'class':'form-control'}),
            'quantity': forms.NumberInput(attrs={'class':'form-control'})
        }

    id = forms.IntegerField(widget=forms.HiddenInput(), required=False)

TicketTypeFormSet = inlineformset_factory(
    Event, TicketType, form=TicketTypeForm,
    extra=1, can_delete_extra=True)

class EventEditForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Zadej název eventu'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Zadej popisek eventu'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Název Eventu',
            'description': 'Popisek Eventu',
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
        fields = ['name']

class CustomAuthenticationForm(AuthenticationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'password']

    def __init__(self, *args, **kwargs):
        super(CustomAuthenticationForm, self).__init__(*args, **kwargs)
        ButtonHolder(
            Submit('submit', 'Přihlásit se', css_class='btn-primary mr-2')
        )

from django.core.exceptions import ValidationError
from allauth.account.forms import SignupForm
from django import forms

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'telephone', 'email', 'date_birth']

class DeliveryAddressForm(forms.ModelForm):
    class Meta:
        model = DeliveryAddress
        fields = ['street', 'number', 'city', 'postal_code', 'country']

class PaymentMethodForm(forms.ModelForm):
    class Meta:
        model = PaymentMethod
        fields = ['card_number', 'name_on_card', 'cvv', 'expiration_date']

class CustomSignupForm(SignupForm):
    username = forms.CharField(max_length=30, label='Uživatelské jméno', required=True)
    first_name = forms.CharField(max_length=30, label='Jméno', required=True)
    last_name = forms.CharField(max_length=30, label='Příjmení', required=True)
    email = forms.EmailField(max_length=254, label='Email', required=True)
    telephone = forms.CharField(max_length=9, label='Telefon', required=True)
    date_birth = forms.DateField(label='Datum narození', required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    image = forms.ImageField(label='Foto', required=False)
    password1 = forms.CharField(label='Heslo', widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label='Potvrdit heslo', widget=forms.PasswordInput, required=True)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise ValidationError("Toto uživatelské jméno je již zaregistrováno.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Tento email je již zaregistrován.")
        return email

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if CustomUser.objects.filter(telephone=telephone).exists():
            raise ValidationError("Toto telefonní číslo je již zaregistrováno.")
        return telephone

    def save(self, request):
        user = super().save(request)
        user.username = self.cleaned_data['username']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.telephone = self.cleaned_data['telephone']
        user.date_birth = self.cleaned_data['date_birth']
        user.image = self.cleaned_data['image']
        user.save()

        # Automaticky přihlásit uživatele
        return user


class UserProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'date_birth', 'organization', 'image']
        widgets = {
            'date_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class SupportForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
    honeypot = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_honeypot(self):
        if self.cleaned_data.get('honeypot'):
            raise ValidationError("Formulář je považován za spam.")
        return self.cleaned_data

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)