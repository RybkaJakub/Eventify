from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.conf import settings
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name='Název organizace', help_text='Zadejte název organizace')
    address = models.TextField(verbose_name='Adresa', help_text='Zadejte adresu organizace')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Datum vytvoření')

    class Meta:
        verbose_name = 'Organizace'
        verbose_name_plural = 'Organizace'

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True,
                                     verbose_name='Organizace', help_text='Vyberte organizaci uživatele')
    email = models.EmailField(unique=True, verbose_name='E-mail', help_text='Zadejte e-mail uživatele')
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


class Event(models.Model):
    name = models.CharField(max_length=200, verbose_name='Název události', help_text='Zadejte název události')
    description = models.TextField(verbose_name='Popis události', help_text='Zadejte popis události')
    day = models.DateField(verbose_name='Den konání eventu', help_text='Zadejte den konání eventu',
                           default=timezone.now)
    start_time = models.TimeField(verbose_name='Čas začátku eventu', help_text='Zadejte čas začátku eventu',
                                  default=timezone.now())
    end_time = models.TimeField(verbose_name='Čas konce eventu', help_text='Zadejte čas konce eventu',
                                default=timezone.now())
    seats = models.PositiveIntegerField(verbose_name='Počet míst', help_text='Zadejte počet dostupných míst')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   verbose_name='Vytvořeno uživatelem', help_text='Vyberte uživatele, který událost vytvořil')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True,
                                     verbose_name='Organizace', help_text='Vyberte organizaci',
                                     error_messages={'null': 'Nejsi v organizaci nemůžeš vytvořit event!'})
    image = models.ImageField(upload_to='event_images/', blank=True, null=True,
                              verbose_name='Obrázek události', help_text='Vyberte obrázek pro událost')

    class Meta:
        verbose_name = 'Událost'
        verbose_name_plural = 'Události'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Pokud je organizace vytvořena uživatelem, nastaví se organizace události na organizaci uživatele
        if self.created_by and not self.organization:
            self.organization = self.created_by.organization
        super(Event, self).save(*args, **kwargs)


class UserEventRegistration(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             verbose_name='Uživatel', help_text='Vyberte uživatele, který se zúčastní události')
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                              verbose_name='Událost', help_text='Vyberte událost, na kterou se uživatel registruje')
    date_registered = models.DateTimeField(auto_now_add=True, verbose_name='Datum registrace')

    class Meta:
        verbose_name = 'Registrace uživatele na událost'
        verbose_name_plural = 'Registrace uživatelů na události'
        unique_together = ('user', 'event')
