from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django import forms

from .forms import EventForm, OrganisationForm
from .models import Event, CustomUser, Organization

admin.site.register(CustomUser)

@admin.register(Organization)
class Organistaion(admin.ModelAdmin):
    form = OrganisationForm
    fields = ['name', 'address']
    widgets = {
        'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    }


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventForm
    readonly_fields = ['image', 'display_logo']  # Přidání display_logo do readonly_fields
    fields = ['name', 'description', 'datetime', 'seats', 'image', 'display_logo']  # display_logo zůstane zde pro zobrazení v detailu
    widgets = {
        'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(editor=request.user)

    def display_logo(self, event):
        if event.image:
            return mark_safe('<img src="{url}" width="{height}">'.format(
                url=event.image.url,
                height=200,
            ))
        else:
            return 'No Image'

    display_logo.short_description = 'Obrázek eventu'
