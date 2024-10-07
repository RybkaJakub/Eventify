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
        if self.created_by and not self.organization:
            self.organization = self.created_by.organization
        super(Event, self).save(*args, **kwargs)

class TicketType(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name='Název vstupenky')
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Cena vstupenky')
    quantity = models.IntegerField(verbose_name='Počet vstupenek')

    def __str__(self):
        return self.event.name

class TicketPurchase(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(verbose_name='Datum vytvoření', default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.event.name} - {self.quantity} vstupenek"
