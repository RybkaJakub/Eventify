from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.conf import settings
from django.db.models.query_utils import logger
from django.utils import timezone
from django.core.exceptions import ValidationError
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeopyError

from django.utils.functional import empty


def validate_postal_code(value):
    if not re.match(r'^\d{3} \d{2}$', value):
        raise ValidationError("PSČ musí být ve formátu 'xxx xx' a obsahovat pouze čísla.")


def validate_card_number(value):
    if not re.match(r'^4\d{15}$', value):
        raise ValidationError("Číslo karty musí být 16 číslic začínajících číslem 4 (Visa).")


def validate_cvv(value):
    if not re.match(r'^\d{3}$', value):
        raise ValidationError("CVV musí být tříciferné číslo.")


def validate_expiration_date(value):
    if value < timezone.now().date():
        raise ValidationError("Datum expirace nesmí být v minulosti.")


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name='Název organizace', help_text='Zadejte název organizace')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Datum vytvoření')

    class Meta:
        verbose_name = 'Organizace'
        verbose_name_plural = 'Organizace'

    def __str__(self):
        return self.name

class OrganizationAddress(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    street = models.TextField(verbose_name="Ulice", help_text="Zadejte ulici")
    number = models.PositiveSmallIntegerField(verbose_name="Číslo popisné", help_text="Zadejte číslo popisné", blank=True, null=True)
    city = models.TextField(verbose_name="Město", help_text="Zadejte město")
    postal_code = models.TextField(validators=[validate_postal_code], verbose_name="PSČ", help_text="Zadejte PSČ")
    country = models.CharField(max_length=255, verbose_name="Stát", help_text="Zadejte stát", default="Česko")

    class Meta:
        verbose_name = 'Adresa Organizace'
        verbose_name_plural = 'Adresa Organizace'


class CustomUser(AbstractUser):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True,
                                     verbose_name='Organizace', help_text='Vyberte organizaci uživatele')
    email = models.EmailField(unique=True, verbose_name='E-mail', help_text='Zadejte e-mail uživatele')
    image = models.ImageField(upload_to='user_images/', blank=True, null=True,
                              verbose_name='Obrázek uživatele', help_text='Vyberte obrázek uživatele')
    date_birth = models.DateField(null=True, blank=True, verbose_name='Datum narození', help_text='Zadejte datum narození')
    phone_validator = RegexValidator(
        regex=r'^\d{9}$',
        message="Telefonní číslo musí obsahovat přesně 9 číslic."
    )
    telephone = models.CharField(
        max_length=9,
        blank=True,
        null=True,
        verbose_name='Telefonní číslo',
        help_text='Zadejte telefonní číslo',
        validators=[phone_validator]
    )

    class Meta:
        verbose_name = 'Uživatel'
        verbose_name_plural = 'Uživatelé'

    def __str__(self):
        return self.email


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street = models.CharField(max_length=255, verbose_name='Ulice', help_text='Zadejte ulici')
    city = models.CharField(max_length=255, verbose_name='Město', help_text='Zadejte město')
    postal_code = models.CharField(max_length=6, verbose_name='PSČ', help_text='Zadejte PSČ')
    country = models.CharField(max_length=255, verbose_name='Země', help_text='Zadejte zemi')

    class Meta:
        verbose_name = 'Adresa'
        verbose_name_plural = 'Adresy'

    def __str__(self):
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('conference', 'Konference'),
        ('festival', 'Festival'),
        ('workshop', 'Workshop'),
        ('sport', 'Sportovní událost'),
        ('social', 'Společenská akce'),
        ('exhibition', 'Výstava'),
        ('concert', 'Koncert'),
        ('online', 'Online událost'),
        ('local', 'Městská akce'),
    ]
    name = models.CharField(max_length=200, verbose_name='Název události', help_text='Zadejte název události')
    description = models.TextField(verbose_name='Popis události', help_text='Zadejte popis události')
    day = models.DateField(verbose_name='Den konání eventu', help_text='Zadejte den konání eventu', default=timezone.now)
    time = models.TimeField(verbose_name='Čas konání eventu', help_text='Zadejte čas konání eventu', default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   verbose_name='Vytvořeno uživatelem', help_text='Vyberte uživatele, který událost vytvořil')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True,
                                     verbose_name='Organizace', help_text='Vyberte organizaci',
                                     error_messages={'null': 'Nejsi v organizaci nemůžeš vytvořit event!'})
    image = models.ImageField(upload_to='event_images/', blank=True, null=True,
                              verbose_name='Obrázek události', help_text='Vyberte obrázek pro událost')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='conference',
    )

    class Meta:
        verbose_name = 'Událost'
        verbose_name_plural = 'Události'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.created_by and not self.organization:
            self.organization = self.created_by.organization
        super(Event, self).save(*args, **kwargs)


class EventAddress(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    street = models.TextField(verbose_name="Ulice", help_text="Zadejte ulici")
    number = models.PositiveSmallIntegerField(verbose_name="Číslo popisné", help_text="Zadejte číslo popisné", blank=True, null=True)
    city = models.TextField(verbose_name="Město", help_text="Zadejte město")
    postal_code = models.TextField(validators=[validate_postal_code], verbose_name="PSČ", help_text="Zadejte PSČ")
    country = models.CharField(max_length=255, verbose_name="Stát", help_text="Zadejte stát", default="Česko")
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        verbose_name = 'Adresa Eventu'
        verbose_name_plural = 'Adresa Eventu'

    def __str__(self):
        return f"{self.street} {self.number}, {self.city}, {self.country}"

    def save(self, *args, **kwargs):
        if not self.latitude or not self.longitude:
            address = f"{self.street} {self.number}, {self.city}, {self.postal_code}, {self.country}"
            geolocator = Nominatim(user_agent="eventify")
            try:
                location = geolocator.geocode(address)
                logger.info(location)
                if location:
                    self.latitude = location.latitude
                    self.longitude = location.longitude
            except GeopyError:
                pass
        super().save(*args, **kwargs)


class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Název vstupenky', help_text='Zadejte název vstupenky')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Cena vstupenky', help_text='Zadejte cenu vstupenky')
    quantity = models.IntegerField(verbose_name='Počet vstupenek', help_text='Zadejte počet vstupenek')
    left = models.IntegerField(verbose_name='Počet zbývajících vstupenek', default=0, editable=False)

    class Meta:
        verbose_name = 'Typ vstupenky'
        verbose_name_plural = 'Typy vstupenek'

    def __str__(self):
        return self.name


class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=255, verbose_name='ID objednávky')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Celková částka', help_text='Zadejte celkovou částku', default=0)
    date = models.DateTimeField(verbose_name='Datum vytvoření', default=timezone.now)

    class Meta:
        verbose_name = 'Objednávka'
        verbose_name_plural = 'Objednávka'

    def __str__(self):
        return f"{self.order_id}"

class PurchasedTickets(models.Model):
    order_id = models.CharField(max_length=255, verbose_name='ID objednávky')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Počet zakoupených vstupenek', help_text='Zadejte počet zakoupených vstupenek')
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True, verbose_name='QR kód', help_text='Vyberte QR kód', default='qr_codes/default.png')

    class Meta:
        verbose_name = 'Zakoupené vstupenky'
        verbose_name_plural = 'Zakoupené vstupenky'

    def __str__(self):
        return f"{self.user.username} - {self.event.name} - {self.quantity} vstupenek"

class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Počet vstupenek', help_text='Zadejte počet vstupenek v košíku')
    total_amount = models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Celková částka', help_text='Zadejte celkovou částku')

    class Meta:
        verbose_name = 'Košík'
        verbose_name_plural = 'Košíky'

class DeliveryAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    street = models.TextField(verbose_name="Ulice", help_text="Zadejte ulici")
    number = models.PositiveSmallIntegerField(verbose_name="Číslo popisné", help_text="Zadejte číslo popisné")
    city = models.TextField(verbose_name="Město", help_text="Zadejte město")
    postal_code = models.TextField(validators=[validate_postal_code], verbose_name="PSČ", help_text="Zadejte PSČ")
    country = models.CharField(max_length=255, verbose_name="Stát", help_text="Zadejte stát", default="Česko")

    class Meta:
        verbose_name = 'Doručovací adresa'
        verbose_name_plural = 'Doručovací adresy'

    def __str__(self):
        return f"{self.street}, {self.city}, {self.country}"

class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Uživatel", help_text="Uživatel, který tuto platební metodu vlastní.")
    name_on_card = models.TextField(default="", verbose_name="Jméno na kartě", help_text="Jméno, které je uvedeno na kartě.", max_length=255)
    card_number = models.TextField(validators=[validate_card_number], verbose_name="Číslo karty", help_text="Zadejte 16místné číslo karty.", max_length=16)
    cvv = models.TextField(validators=[validate_cvv], verbose_name="CVV", help_text="Bezpečnostní kód na zadní straně karty.", max_length=3)
    expiration_date = models.DateField(verbose_name="Datum expirace", help_text="Datum expirace karty ve formátu MM/RR.", null=True)

    class Meta:
        verbose_name = 'Platební metoda'
        verbose_name_plural = 'Platební metody'

    def __str__(self):
        return f"{self.name_on_card}, {self.card_number}, {self.expiration_date}"