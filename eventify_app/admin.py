from django.contrib import admin
from django.utils.safestring import mark_safe

from .forms import EventForm, OrganizationForm
from .models import Event, CustomUser, Organization, TicketType, EventAddress, OrganizationAddress, Order, \
    PurchasedTickets

admin.site.register(CustomUser)

class OrganizationAddressInline(admin.TabularInline):
    model = OrganizationAddress

@admin.register(Organization)
class Organization(admin.ModelAdmin):
    form = OrganizationForm
    fields = ['name']
    inlines = [OrganizationAddressInline]

@admin.register(Order)
class Order(admin.ModelAdmin):
    model = Order
    fields = ['order_id', 'total_amount', 'date', 'user']

@admin.register(PurchasedTickets)
class PurchasedTickets(admin.ModelAdmin):
    model = PurchasedTickets
    fields = ['order_id', 'quantity', 'qr_code', 'event', 'ticket_type', 'user']

class TicketTypeInline(admin.TabularInline):
    model = TicketType

class EventAddressInline(admin.TabularInline):
    model = EventAddress

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    form = EventForm
    readonly_fields = ['image', 'display_logo']
    fields = ['name', 'description', 'organization', 'day', 'image', 'display_logo']
    inlines = [TicketTypeInline, EventAddressInline]

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