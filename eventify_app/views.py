import os
import json
import logging
import qrcode
from io import BytesIO
from datetime import datetime, timedelta
from calendar import monthrange, Calendar

from captcha.helpers import captcha_image_url
from captcha.models import CaptchaStore
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.core.files.base import ContentFile
from django.core.mail import send_mail, EmailMessage
from django.db.models import Q
from django.forms import modelformset_factory
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import resolve, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from django.views import View
from django.views.generic import (
    DetailView, UpdateView, DeleteView, CreateView, ListView, TemplateView
)
from weasyprint import HTML
from geopy import Nominatim
from geopy.distance import geodesic
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from .models import (
    CustomUser, Cart, DeliveryAddress, PaymentMethod, PurchasedTickets,
    Order, Organization, TicketType, Address, Event, EventAddress
)
from .forms import (
    UserProfileEditForm, PaymentMethodForm, ContactForm, SupportForm,
    EventAddressForm, TicketTypeForm, EventForm, TicketTypeFormSet,
    CustomUserForm, DeliveryAddressForm
)

logger = logging.getLogger(__name__)

def send_email(html_template, context):
    from_email = settings.EMAIL_HOST_USER
    subject = context.get('subject')
    to_email = context.get('to_email')
    cc = context.get('cc')
    bcc = context.get('bcc')
    attachments = context.get('attachments')

    if not to_email:
        raise ValueError("The 'to_email' address must be provided and cannot be empty.")
    elif not isinstance(to_email, list):
        to_email = [to_email]

    try:
        html_message = render_to_string(html_template, context)
        message = EmailMessage(subject=subject, body=html_message, from_email=from_email, to=to_email, cc=cc, bcc=bcc,
                               attachments=attachments)
        message.content_subtype = 'html'
        result = message.send()
        logger.info(f"Sending email to {', '.join(to_email)} with subject: {subject} - Status {result}")
    except Exception as e:
        logger.info(f"Sending email to {', '.join(to_email)} with subject: {subject} - Status 0")
        logger.exception(e)


def index(request):
    registered_events = []
    organization_events = []
    divider_rendered = False
    profile_picture = ''
    has_picture = False

    now = timezone.now()
    upcoming_events = Event.objects.filter(
        Q(day__gt=now.date()) | (Q(day=now.date()) & Q(time__gt=now))
    ).order_by('day', 'time')

    if request.user.is_authenticated:
        registered_events = PurchasedTickets.objects.filter(user=request.user).distinct('event')
        organization_events = Event.objects.filter(organization=request.user.organization)
        social_accounts = SocialAccount.objects.filter(user=request.user)
        profile_picture = UserProfileView.get_user_profile_picture(request, social_accounts)
        if profile_picture:
            has_picture = True
        for group in request.user.groups.all():
            if group.name == "editor" or group.name == "admin":
                divider_rendered = True
                break

    events = Event.objects.all()

    # Načti všechny souřadnice pro události
    event_addresses = EventAddress.objects.all()

    # Vytvoř slovník pro souřadnice podle event_id
    event_address_dict = {address.event.id: address for address in event_addresses}

    # Předání událostí a jejich souřadnic
    events_data = []
    for event in events:
        address = event_address_dict.get(event.id)
        latitude = address.latitude if address else None
        longitude = address.longitude if address else None

        # Převod datumu a času na řetězec
        event_day = event.day.strftime('%Y-%m-%d') if event.day else None
        event_time = event.time.strftime('%H:%M') if event.time else None

        events_data.append({
            'name': event.name,
            'day': event_day,
            'time': event_time,
            'category': event.category,
            'description': event.description,
            'image': event.image.url if event.image else '',
            'latitude': latitude,
            'longitude': longitude,
            'id': event.id,
        })

    # Převod na JSON řetězec
    events_json = json.dumps(events_data)

    context = {
        'divider_rendered': divider_rendered,
        'upcoming_events': upcoming_events,
        'organization_events': organization_events,
        'registered_events': registered_events,
        'profile_picture': profile_picture,
        'has_picture': has_picture,
        'user': request.user,
        'events_json': events_json
    }

    return render(request, 'index.html', context=context)


class EventManagerView(PermissionRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_manager.html'
    permission_required = 'eventify_app.change_event'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        has_picture = False
        organization = user.organization

        in_organization = True if organization else False

        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True

        context['organization'] = organization
        context['in_organization'] = in_organization
        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture
        events = Event.objects.filter(organization=organization)

        events_with_addresses = []
        for event in events:
            event_address = EventAddress.objects.filter(
                event=event).first()
            events_with_addresses.append({
                'event': event,
                'address': event_address
            })

        context['events_with_addresses'] = events_with_addresses
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name

        return context

class EventInline():
    form_class = EventForm
    model = Event
    template_name = "events/event_manager_create.html"

    def __init__(self):
        self.object = None

    def form_valid(self, form):
        named_formsets = self.get_named_formsets()
        if not all((x.is_valid() for x in named_formsets.values())):
            return self.render_to_response(self.get_context_data(form=form))

        form.instance.created_by = self.request.user
        self.object = form.save()

        # Uložení adresy eventu
        event_address_form = self.get_event_address_form()
        if event_address_form.is_valid():
            event_address = event_address_form.save(commit=False)
            event_address.event = self.object
            event_address.save()
        else:
            return self.render_to_response(
                self.get_context_data(form=form, event_address_form=event_address_form)
            )

        # Uložení ticket typů
        for name, formset in named_formsets.items():
            formset_save_func = getattr(self, f'formset_{name}_valid', None)
            if formset_save_func is not None:
                formset_save_func(formset)
            else:
                formset.save()

        return redirect('event_manager')

    def formset_ticket_types_valid(self, formset):
        ticket_types = formset.save(commit=False)
        for ticket_type in ticket_types:
            ticket_type.event = self.object
            ticket_type.left = ticket_type.quantity
            ticket_type.save()

    def get_event_address_form(self):
        if self.request.method == 'POST':
            return EventAddressForm(self.request.POST)
        return EventAddressForm()


class EventCreateView(EventInline, CreateView, LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = 'events.add_event'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        ctx['categories'] = Event.CATEGORY_CHOICES

        # Přidání formuláře pro adresu eventu
        if 'event_address_form' not in ctx:
            ctx['event_address_form'] = self.get_event_address_form()

        # Přidání formsetů pro ticket types
        ctx['named_formsets'] = self.get_named_formsets()

        # Získání profilového obrázku
        profile_picture = UserProfileView.get_user_profile_picture(
            self.request, SocialAccount.objects.filter(user=self.request.user)
        )
        ctx['profile_picture'] = profile_picture
        ctx['has_picture'] = bool(profile_picture)

        return ctx

    def get_named_formsets(self):
        if self.request.method == 'GET':
            return {'ticket_types': TicketTypeFormSet(prefix='ticket_types')}
        return {'ticket_types': TicketTypeFormSet(self.request.POST, prefix='ticket_types')}

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        event_address_form = self.get_event_address_form()
        named_formsets = self.get_named_formsets()

        if form.is_valid() and event_address_form.is_valid() and all(
                fs.is_valid() for fs in named_formsets.values()
        ):
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class EventUpdateView(LoginRequiredMixin, UpdateView):
    template_name = 'events/event_manager_edit.html'
    model = Event
    form_class = EventForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Načteme formulář pro EventAddress
        context['categories'] = Event.CATEGORY_CHOICES
        event_address_form = self.get_event_address_form()
        context['event_address_form'] = event_address_form
        context['event'] = self.object
        context['user'] = self.request.user
        context['event_address'] = EventAddress.objects.filter(event=self.object).first()

        return context

    def get_event_address_form(self):
        # Získáme EventAddress spojený s tímto Event objektem
        event_address = EventAddress.objects.filter(event=self.object).first()

        # Pokud neexistuje žádná adres, vytvoříme prázdnou instanci
        if not event_address:
            event_address = EventAddress(event=self.object)

        # Pokud je POST požadavek, předáme data formuláře, jinak použijeme stávající instanci
        if self.request.method == 'POST':
            return EventAddressForm(self.request.POST, instance=event_address)
        return EventAddressForm(instance=event_address)

    def post(self, request, *args, **kwargs):
        # Načteme objekt Event
        self.object = self.get_object()  # Získání objektu Event podle primárního klíče

        # Načteme formuláře
        form = self.get_form()
        event_address_form = self.get_event_address_form()

        # Pokud všechny formuláře a formsety jsou validní, pokračujeme
        if form.is_valid() and event_address_form.is_valid():
            # Uložení Eventu
            self.object = form.save(commit=False)  # Uložení bez commit, aby se neuložil dřív
            self.object.save()

            # Uložení EventAddress
            event_address = event_address_form.save(commit=False)
            event_address.event = self.object  # Přiřazení Eventu k adrese
            event_address.save()

            messages.success(request, "Událost byla úspěšně upravena.")

            # Přesměrování na seznam eventů po úspěšném uložení
            return redirect('edit_event' , pk=self.object.pk)

        # Pokud nějaký formulář není validní, vykreslíme stránku s chybami
        context = self.get_context_data(form=form, event_address_form=event_address_form)
        return self.render_to_response(context)


class EditTicketView(View):

    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        # Formset pro existující TicketType objekty
        TicketTypeFormSet = modelformset_factory(TicketType, form=TicketTypeForm, extra=0)
        formset = TicketTypeFormSet(queryset=TicketType.objects.filter(event=event), prefix='ticket_types')

        return render(request, 'events/event_manager_edit_ticket.html', {'formset': formset, 'event': event})

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk)

        # Formset pro POST data
        TicketTypeFormSet = modelformset_factory(TicketType, form=TicketTypeForm, extra=0)
        formset = TicketTypeFormSet(request.POST, queryset=TicketType.objects.filter(event=event),
                                    prefix='ticket_types')

        if formset.is_valid():
            tickets = formset.save(commit=False)  # Uloží pouze instance bez jejich uložení do DB
            for ticket in tickets:
                ticket.event = event  # Ručně nastavíme `event`
                ticket.save()  # Uložíme do DB
            messages.success(request, "Vstupenky byly úspěšně uloženy.")
            return redirect('edit_ticket', pk=event.pk)
        else:
            # Debugging: vypíšeme chyby formulářů
            for form in formset:
                print(form.errors)
            messages.error(request, "Došlo k chybě při ukládání vstupenek.")
            return render(request, 'events/event_manager_edit_ticket.html', {'formset': formset, 'event': event})


class AddTicketView(View):
    def post(self, request, event_pk):
        # Načtení eventu nebo vyvolání 404 chyby, pokud neexistuje
        event = Event.objects.filter(pk=event_pk).first()

        # Vytvoření nového typu vstupenky
        TicketType.objects.create(
            event=event,
            name='Nový typ vstupenky',
            price=0,
            quantity=0,
            left=0
        )

        # Přesměrování zpět na úpravu vstupenek pro daný event
        return redirect('edit_ticket', pk=event.pk)


class DeleteTicketView(View):
    def post(self, request, ticket_id):
        try:
            ticket = get_object_or_404(TicketType, pk=ticket_id)
            ticket.delete()
            messages.success(request, "Vstupenka byla úspěšně smazána.")
            return redirect('edit_ticket', pk=ticket.event.pk)
        except Exception as e:
            messages.error(request, "Nepodařilo se smazat vstupenku.")
            return redirect('edit_ticket', pk=ticket.event.pk)


from django.shortcuts import get_object_or_404


class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_manager_delete.html'
    context_object_name = 'event'
    success_url = '/eventify_app/eventmanager/'
    permission_required = 'eventify_app.delete_event'

    def test_func(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.image and self.object.image.path:
            try:
                if os.path.isfile(self.object.image.path):  # Ověříme, že soubor existuje
                    os.remove(self.object.image.path)  # Smažeme obrázek
            except Exception as e:
                print(f"Chyba při mazání obrázku: {e}")  # Logování chyby (pouze pro ladění)
        return super().delete(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True
        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['isAdmin'] = False
        context['userOrganization'] = False
        context['purchasedTickets'] = PurchasedTickets.objects.filter(event=self.object)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        context['ticket_types'] = TicketType.objects.filter(event=self.object)
        context['event_address'] = EventAddress.objects.filter(event=self.object).first()

        has_picture = False

        auth = self.request.user.is_authenticated
        context['isAuth'] = auth

        if auth:
            profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                       SocialAccount.objects.filter(
                                                                           user=self.request.user))
            if profile_picture:
                has_picture = True
            context['has_picture'] = has_picture
            context['profile_picture'] = profile_picture
            # Pouze pro přihlášené uživatele
            context['userTickets'] = PurchasedTickets.objects.filter(
                user=self.request.user,
                event=self.object
            )
            context['registered'] = PurchasedTickets.objects.filter(
                user=self.request.user,
                event=self.object
            ).exists()
            if self.object.organization == getattr(self.request.user, 'organization', None):
                context['userOrganization'] = True

            for group in self.request.user.groups.all():
                if group.name in ["editor", "admin"]:
                    context['isAdmin'] = True
                    break
        else:
            context['userTickets'] = None
            context['registered'] = False

        return context

class MyProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'account/myprofile.html'

    def get_user_profile_picture(self, social_accounts):
        # Získání profilového obrázku podle priorit
        if social_accounts:
            for account in social_accounts:
                extra_data = account.extra_data  # Uložení extra_data do proměnné
                if account.provider == 'discord':
                    # Opraveno: Přístup k hodnotám slovníku
                    url = f'https://cdn.discordapp.com/avatars/{extra_data["id"]}/{extra_data["avatar"]}.png?size=240'
                    return url
                if account.provider == 'github':
                    url = f'https://avatars.githubusercontent.com/u/{extra_data["id"]}'
                    return url
                if account.provider == 'google':
                    return extra_data.get("picture", '')  # Použij get pro bezpečný přístup k hodnotě

        return ''  # Pokud nemá žádný sociální účet, vrátí se uživatelský obrázek

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.clear()
        user = self.request.user
        context['user'] = user
        context['address'] = Address.objects.filter(user=user)
        context['email_confirmed'] = EmailAddress.objects.filter(user=user, verified=True).exists()
        context['social_accounts'] = SocialAccount.objects.filter(user=user)
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True
        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture
        return context


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'account/profile.html'

    def get_user_profile_picture(self, social_accounts):
        # Získání profilového obrázku podle priorit
        if social_accounts:
            for account in social_accounts:
                extra_data = account.extra_data  # Uložení extra_data do proměnné
                if account.provider == 'discord':
                    # Opraveno: Přístup k hodnotám slovníku
                    url = f'https://cdn.discordapp.com/avatars/{extra_data["id"]}/{extra_data["avatar"]}.png?size=240'
                    return url
                if account.provider == 'github':
                    url = f'https://avatars.githubusercontent.com/u/{extra_data["id"]}'
                    return url
                if account.provider == 'google':
                    return extra_data.get("picture", '')  # Použij get pro bezpečný přístup k hodnotě

        return ''  # Pokud nemá žádný sociální účet, vrátí se uživatelský obrázek

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.clear()
        vieweduser = get_object_or_404(CustomUser, pk=self.kwargs['pk'])
        user = self.request.user
        context['user'] = user
        context['vieweduser'] = vieweduser
        context['address'] = Address.objects.filter(user=vieweduser)
        context['email_confirmed'] = EmailAddress.objects.filter(user=vieweduser, verified=True).exists()
        context['social_accounts'] = SocialAccount.objects.filter(user=vieweduser)
        viewed_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                  SocialAccount.objects.filter(user=vieweduser))
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True
        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture
        context['viewed_picture'] = viewed_picture
        return context


class UserProfileEditView(UpdateView):
    model = CustomUser
    form_class = UserProfileEditForm
    template_name = 'account/edit_my_profile.html'
    success_url = reverse_lazy('myprofile')

    def get_object(self):
        return self.request.user

    def form_invalid(self, form):
        messages.error(self.request, "Opravit chyby ve formuláři.")
        return super().form_invalid(form)


class MyEventsListView(ListView):
    model = Order  # <--- ZMĚNA: stránkujeme objednávky
    template_name = 'events/my_tickets.html'
    context_object_name = 'orders'  # <--- V šabloně pak iteruješ přes 'orders'
    paginate_by = 6  # <--- 2 objednávky na stránku

    def get_queryset(self):
        """Vrátí objednávky pro přihlášeného uživatele, seřazené od nejnovější."""
        if not self.request.user.is_authenticated:
            return Order.objects.none()
        return Order.objects.filter(user=self.request.user).order_by('-date')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        # Profilový obrázek
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(
            self.request, SocialAccount.objects.filter(user=self.request.user)
        )
        if profile_picture:
            has_picture = True

        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture
        context['isAuth'] = self.request.user.is_authenticated

        # K objednávkám přidáme rovnou tikety do `order.tickets`
        for order in context['orders']:
            purchasedTickets = PurchasedTickets.objects.filter(order_id=order.order_id)
            order.tickets = purchasedTickets

        return context


@login_required
def purchase_ticket(request, pk):
    if request.method == 'POST':
        event_id = pk  # Získej event_id z formuláře
        ticket_type_id = request.POST.get('ticket_type')
        quantity = int(request.POST.get('quantity'))

        event = get_object_or_404(Event, id=event_id)
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id)

        if ticket_type.left < quantity:
            messages.error(request,
                           f'Nedostatečný počet vstupenek typu {ticket_type.name}. Zbývá pouze {ticket_type.left} vstupenek.')
            return redirect('event_detail', pk=event_id)

        total_amount = ticket_type.price * quantity

        # Zjisti, jestli už položka existuje v košíku
        cart_item = Cart.objects.filter(user=request.user, event=event, ticket_type=ticket_type).first()

        if cart_item:
            # Aktualizuj existující položku
            cart_item.quantity += quantity
            cart_item.total_amount += total_amount
            cart_item.save()
        else:
            # Vytvoř novou položku v košíku
            Cart.objects.create(
                user=request.user,
                event=event,
                ticket_type=ticket_type,
                quantity=quantity,
                total_amount=total_amount
            )

        messages.success(request, f'Úspěšně jste přidali do košíku {quantity} vstupenek na event "{event.name}".')
        return redirect('event_detail', pk=event_id)

    return redirect('index')


class CartView(LoginRequiredMixin, TemplateView):
    template_name = "account/cart.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        items = Cart.objects.filter(user=user)
        context['items'] = items
        total_price = sum(item.total_amount for item in items)
        context['total_price'] = total_price

        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True

        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture

        return context

    def post(self, request, *args, **kwargs):
        items = Cart.objects.filter(user=request.user)
        for item in items:
            quantity = request.POST.get(f'quantity_{item.id}')
            if quantity:
                quantity = int(quantity)
                if quantity > item.ticket_type.left:
                    messages.error(request,
                                   f'Nemůžete si objednat více než {item.ticket_type.left} vstupenek pro {item.ticket_type.name}.')
                    return redirect('cart')
                item.quantity = quantity
                item.total_amount = item.ticket_type.price * quantity
                item.save()

        messages.success(request, 'Košík byl úspěšně aktualizován.')
        return redirect('cart')

class CartInformationsView(LoginRequiredMixin, TemplateView):
    template_name = "account/cart_informations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user

        delivery_address = DeliveryAddress.objects.filter(user=user).first()
        context['delivery_address'] = delivery_address
        context['user_form'] = CustomUserForm(instance=user)
        context['address_form'] = DeliveryAddressForm(instance=delivery_address)

        # Kontrola pro profilový obrázek
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True

        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture

        context['new_message'] = False

        return context

    def post(self, request, *args, **kwargs):
        user_form = CustomUserForm(request.POST, instance=request.user)
        address_instance = DeliveryAddress.objects.filter(user=request.user).first() or DeliveryAddress(
            user=request.user)
        address_form = DeliveryAddressForm(request.POST, instance=address_instance)
        if user_form.is_valid() and address_form.is_valid():
            user_form.save()
            address_form.save()
            messages.success(request, 'Vaše informace byly úspěšně aktualizovány.')
            context = self.get_context_data()
            context['user_form'] = user_form
            context['address_form'] = address_form
            context['new_message'] = True
            return self.render_to_response(context)
        else:
            messages.error(request, 'Chyba při aktualizaci informací. Zkontrolujte zadání.')

            # Vrátí formuláře s chybami
        context = self.get_context_data()
        context['user_form'] = user_form  # Vrátí formuláře s chybami
        context['address_form'] = address_form
        context['new_message'] = True
        return self.render_to_response(context)


class CartPaymentView(LoginRequiredMixin, TemplateView):
    template_name = "account/cart_payment.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        # Načítání metody platby a formuláře pro zobrazení a úpravy
        payment_method = PaymentMethod.objects.filter(user=user).first()
        context['payment_method'] = payment_method
        context['payment_form'] = PaymentMethodForm(instance=payment_method)

        # Načítání profilové fotografie
        profile_picture = UserProfileView.get_user_profile_picture(
            self.request, SocialAccount.objects.filter(user=user)
        )
        context['profile_picture'] = profile_picture
        context['has_picture'] = bool(profile_picture)

        return context

    def post(self, request, *args, **kwargs):
        payment_method = PaymentMethod.objects.filter(user=request.user).first() or PaymentMethod(user=request.user)
        payment_form = PaymentMethodForm(request.POST, instance=payment_method)

        if payment_form.is_valid():
            payment_form.save()
            messages.success(request, 'Vaše platební údaje byly úspěšně aktualizovány.')
            context = self.get_context_data()
            context['payment_form'] = payment_form
            context['new_message'] = True
            return self.render_to_response(context)
        else:
            messages.error(request, 'Chyba při aktualizaci platebních údajů. Zkontrolujte zadání.')

        # Vrátí formulář s chybami
        context = self.get_context_data()
        context['payment_form'] = payment_form
        context['new_message'] = True
        return self.render_to_response(context)

import random

class CartConfirmationView(LoginRequiredMixin, TemplateView):
    template_name = "account/cart_confirmation.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        items = Cart.objects.filter(user=user)
        context['items'] = items
        total_price = sum(item.total_amount for item in items)
        context['total_price'] = total_price

        payment_method = PaymentMethod.objects.filter(user=user).first()
        context['payment_method'] = payment_method
        delivery_address = DeliveryAddress.objects.filter(user=user).first()
        context['delivery_address'] = delivery_address

        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True

        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture

        return context

    def generate_order_id(self):
        year = timezone.now().year  # Aktuální rok
        part1 = ''.join([str(random.randint(0, 9)) for _ in range(4)])  # Čtyři čísla
        part2 = ''.join([str(random.randint(0, 9)) for _ in range(4)])  # Čtyři čísla
        part3 = ''.join([str(random.randint(0, 9)) for _ in range(4)])  # Čtyři čísla

        return f"{year}-{part1}-{part2}-{part3}"

    def post(self, request, *args, **kwargs):
        user = request.user
        delivery_address = DeliveryAddress.objects.filter(user=user).first()
        payment_method = PaymentMethod.objects.filter(user=user).first()
        items = Cart.objects.filter(user=user)
        total_amount = sum(item.total_amount for item in items)
        order_id = self.generate_order_id()
        address = user.email
        subject = "Objednávka vstupenek"

        if delivery_address and payment_method and items:
            # Vytvoření objednávky
            order = Order.objects.create(
                user=user,
                order_id=order_id,
                total_amount=total_amount,
                date=timezone.now()
            )

            # Přidání vstupenek k objednávce
            for item in items:
                new_ticket = PurchasedTickets.objects.create(
                    order_id=order_id,
                    user=user,
                    event=item.event,
                    ticket_type=item.ticket_type,
                    quantity=item.quantity,
                )

                data = {
                    "order_id": order_id,
                    "ticket_id": item.id,
                    "total_price": float(item.quantity * item.ticket_type.price),
                    "quantity": item.quantity,
                    "event_name": item.event.name
                }

                # Serializace dat do JSON
                qr_data = json.dumps(data)

                # Vytvoření QR kódu
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)

                # Vytvoření obrázku QR kódu
                img = qr.make_image(fill_color="black", back_color="white")

                # Uložení QR kódu do paměti
                buffer = BytesIO()
                img.save(buffer, format="PNG")
                buffer.seek(0)

                # Uložení do pole `qr_code`
                new_ticket.qr_code.save(f"{order_id}_{item.id}.png", ContentFile(buffer.read()), save=False)
                buffer.close()

                new_ticket.save()

            # Odebrání vstupenek z košíku
            items.delete()  # QuerySet nemá `save()`

            # Odeslání emailu
            tickets = PurchasedTickets.objects.filter(order_id=order_id)

            if address and subject:
                subject = f'Potvrzení nákupu vstupenek objednávky {order.order_id} - Eventify'
                html_message = render_to_string(
                    'email/email.html',
                    {
                        'request': request,
                        'tickets': tickets,
                        'user_name': f'{user.first_name} {user.last_name}'
                    }
                )
                plain_message = strip_tags(html_message)
                from_email = settings.EMAIL_HOST_USER
                to_email = [address]

                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=from_email,
                    to=to_email
                )
                email.content_subtype = 'html'

                # 1) Zavoláme tvou funkci, která vrací HttpResponse (PDF)
                pdf_response = generate_ticket_pdf(request, order.id)  # Tohle pravděpodobně vrací HttpResponse

                # 2) Získáme binární obsah PDF
                pdf_content = pdf_response.content  # .content = bytes v těle odpovědi

                # 3) Přidáme jako přílohu
                email.attach(f"{order.order_id}.pdf", pdf_content, "application/pdf")

                # 4) Odeslání
                email.send()

            return redirect('index')
        else:
            return redirect('index')


def generate_ticket_pdf(request, order_id):
    # Načtěte objednávku a tickety
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse('Objednávka nenalezena', status=404)

    tickets = PurchasedTickets.objects.filter(order_id=order.order_id)

    # Renderujte HTML šablonu s daty
    html_content = render_to_string('tickets/pdf_template.html', {'tickets': tickets, 'order': order})

    # Vytvoření PDF pomocí WeasyPrint
    pdf = HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf()

    # Vytvořte HTTP odpověď
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order.order_id}.pdf"'

    return response


class RemoveItemView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(Cart, id=item_id, user=request.user)
        item.delete()
        return redirect('cart')


class ClearCartView(LoginRequiredMixin, View):
    def post(self, request):
        Cart.objects.filter(user=request.user).delete()
        return redirect('cart')

class EventsListView(ListView):
    model = Event
    template_name = 'events/events_list.html'

    # context_object_name nepoužijeme,
    # aby Django použilo výchozí jméno: "object_list" + "page_obj", "paginator", "is_paginated".
    paginate_by = 3  # Tady nastavíš, kolik eventů na stránku

    def get_queryset(self):
        events = super().get_queryset()
        name_filter = self.request.GET.get('name')
        date_filter = self.request.GET.get('date')
        location_filter = self.request.GET.get('location')
        category_filter = self.request.GET.get('category')

        # Filtrování
        if name_filter:
            events = events.filter(name__icontains=name_filter)
        if date_filter:
            events = events.filter(day=date_filter)
        if category_filter:
            events = events.filter(category=category_filter)
        if location_filter:
            geolocator = Nominatim(user_agent="eventify")
            location = geolocator.geocode(location_filter)
            if location:
                user_location = (location.latitude, location.longitude)
                event_addresses = EventAddress.objects.all()
                nearby_events = []
                for address in event_addresses:
                    if address.latitude and address.longitude:
                        event_location = (address.latitude, address.longitude)
                        if geodesic(user_location, event_location).km <= 20:
                            nearby_events.append(address.event.id)
                events = events.filter(id__in=nearby_events)

        return events

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        category_filter = self.request.GET.get('category', '')
        categories = dict(Event.CATEGORY_CHOICES)
        selected_category_label = categories.get(category_filter, '')

        context.update({
            'name_filter': self.request.GET.get('name', ''),
            'date_filter': self.request.GET.get('date', ''),
            'location_filter': self.request.GET.get('location', ''),
            'category_filter': category_filter,
            'selected_category_label': selected_category_label,
            'categories': Event.CATEGORY_CHOICES,
        })
        return context


class TermsOfUseView(TemplateView):
    template_name = 'informations/terms_of_use.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date'] = timezone.now()
        return context


class PrivacyPolicy(TemplateView):
    template_name = 'informations/privacy_policy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date'] = timezone.now()
        return context


class Faq(TemplateView):
    template_name = 'informations/frequently_asked.html'


class AboutUs(TemplateView):
    template_name = 'informations/about_us.html'

    def get_context_data(self, **kwargs):
        team_members = [
            {
                "name": "Jan Novák",
                "role": "CEO & Zakladatel",
                "bio": (
                    "Jan, náš zakladatel, si vždy kladl za cíl propojit kreativitu s byznysovou precizností. "
                    "Po letech strávených v zahraničí se vrátil domů, aby zde vybudoval inovativní platformu, "
                    "která změní způsob, jakým lidé plánují a prožívají eventy. Jan věří, že každá akce má "
                    "moci přinášet nejen zábavu, ale i trvalý dopad na komunitu a společnost."
                ),
                "image": "/static/img/novak.jpeg"
            },
            {
                "name": "Petra Svobodová",
                "role": "Projektová manažerka",
                "bio": (
                    "Petra je zkušená koordinátorka s vášní pro organizaci, harmonogramy a detailní plánování. "
                    "V Eventify dohlíží na rozmanité projekty a zajišťuje, že spolupráce mezi našimi týmy probíhá "
                    "hladce. Její přirozená schopnost vést a motivovat ostatní je jedním z hlavních důvodů, proč "
                    "každý event, který se u nás připravuje, dopadne nad očekávání."
                ),
                "image": "/static/img/svobodova.png"
            },
            {
                "name": "Tomáš Dvořák",
                "role": "Marketingový specialista",
                "bio": (
                    "Tomáš je odborník na digitální marketing, který má za sebou úspěšné kampaně v různých "
                    "sektorech od e-commerce až po neziskové projekty. V Eventify zodpovídá za komunikaci s "
                    "veřejností, budování brandu a online propagaci akcí, které pomáháme realizovat. Jeho "
                    "kreativní nápady a precizní strategie přitahují pozornost stále širšího publika."
                ),
                "image": "/static/img/dvorak.jpeg"
            },
            {
                "name": "Lucie Procházková",
                "role": "Hlavní koordinátorka eventů",
                "bio": (
                    "Lucie se specializuje na organizaci středních a velkých akcí, ať už jde o firemní konference "
                    "nebo kulturní festivaly pro tisíce lidí. Jejím posláním je propojovat dovednosti napříč týmy, "
                    "udržovat vysokou kvalitu služeb a podporovat všechny členy produkce, aby z akce vznikl "
                    "jedinečný zážitek. Vystudovala ekonomii i kulturní management, a tyto dvě oblasti dokáže "
                    "skvěle spojit v jednom projektu."
                ),
                "image": "/static/img/prochazkova.jpg"
            },
            {
                "name": "David Horák",
                "role": "Vedoucí vývojového týmu",
                "bio": (
                    "David je duší našeho technického řešení. Za sebou má praxi z několika softwarových "
                    "společností, kde vedl vývoj pokročilých webových aplikací. V Eventify je zodpovědný "
                    "za stabilitu platformy, návrh architektury a implementaci nových funkcí, které posouvají "
                    "celý projekt na vyšší úroveň. Miluje moderní technologie, open-source a agilní metody."
                ),
                "image": "/static/img/horak.jpg"
            },
            {
                "name": "Alena Králová",
                "role": "Head of Customer Experience",
                "bio": (
                    "Alena se stará o to, aby zkušenosti a dojmy všech uživatelů Eventify byly naprosto špičkové. "
                    "Kombinuje data, průzkumy a lidskou empatii, aby vylepšovala uživatelské rozhraní a "
                    "podporovala dlouhodobou spokojenost. Je přesvědčená, že úspěch projektu stojí a padá s tím, "
                    "jak moc si zákazník cení komfortu a podpory, kterou mu poskytujeme."
                ),
                "image": "/static/img/kralova.jpg"
            },
            {
                "name": "Marek Čermák",
                "role": "Produktový designér",
                "bio": (
                    "Marek je člověkem, který stojí za vizuální identitou a funkčním designem Eventify. "
                    "Od drátových modelů, přes uživatelské testy, až k finálnímu prototypu – Marek má v oku "
                    "nejen estetiku, ale i přirozenou použitelnost. Neustále zkoumá nejnovější trendy v "
                    "UI/UX a nebojí se experimentovat, pokud to může přinést lepší zážitek pro uživatele."
                ),
                "image": "/static/img/cermak.jpg"
            },
            {
                "name": "Karolína Veselá",
                "role": "Senior Event Manager",
                "bio": (
                    "Karolína se vyzná v produkci kulturních akcí, přednášek i gastronomických festivalů. "
                    "V Eventify pomáhá klientům s plánováním harmonogramů, tvorbou rozpočtů i nastavováním "
                    "správných procesů, aby každý event proběhl včas a bez stresu. Její organizační schopnosti "
                    "a empatický přístup k lidem z ní dělají srdce mnoha úspěšných projektů."
                ),
                "image": "/static/img/vesela.jpg"
            },
            {
                "name": "Pavel Mach",
                "role": "Finanční strateg",
                "bio": (
                    "Pavel má na starost celkovou finanční strategii a plánování rozpočtů pro rozvoj Eventify. "
                    "Jeho hlavním cílem je hledat dlouhodobě udržitelné obchodní modely, které nám umožní "
                    "financovat inovace a současně udržet příznivé ceny pro uživatele. Před nástupem do Eventify "
                    "působil jako finanční ředitel ve dvou významných startupech."
                ),
                "image": "/static/img/mach.jpg"
            },
            {
                "name": "Denisa Zahradníková",
                "role": "PR a Media Relations",
                "bio": (
                    "Denisa se vyzná v tom, jak o vás dát vědět světu. Stará se o mediální komunikaci a "
                    "zajišťuje, že se o našich nových funkcích a úspěšných projektech dozvědí nejen novináři, "
                    "ale i široká veřejnost. Díky svým kontaktům dokáže pro Eventify i naše klienty zajistit "
                    "viditelnost v online i offline médiích."
                ),
                "image": "/static/img/zahradnikova.jpg"
            },
            {
                "name": "Michal Nedvěd",
                "role": "Backend Developer",
                "bio": (
                    "Michal je backendový mág, který se stará o hladký chod databází, API a veškeré logiky "
                    "na pozadí. Je zastáncem clean code a optimalizovaných dotazů, aby naše aplikace fungovala "
                    "rychle i při tisících požadavků za minutu. Vždy se snaží přijít s elegantním řešením "
                    "i na zdánlivě složité problémy."
                ),
                "image": "/static/img/nedved.jpg"
            },
            {
                "name": "Nikola Tichá",
                "role": "Konzultantka pro firemní akce",
                "bio": (
                    "Nikola se specializuje na velké firemní konference, gala večery a teambuildingy. "
                    "Jejím úkolem je sestavit koncept akce, najít vhodné dodavatele a sladit branding s "
                    "hlavní myšlenkou. Díky svému vřelému a profesionálnímu přístupu dokáže proměnit i "
                    "formální večer v přátelskou a inspirativní událost."
                ),
                "image": "/static/img/ticha.jpg"
            },
            {
                "name": "Jiří Vlk",
                "role": "Analytik a Data Scientist",
                "bio": (
                    "Jiří se věnuje analýze dat a vyhodnocování všech procesů, které v Eventify probíhají. "
                    "Na základě čísel a metrik navrhuje způsoby, jak zlepšit uživatelskou spokojenost, "
                    "zvyšovat efektivitu plánování akcí a rozšiřovat tržní potenciál. Tím pomáhá "
                    "snižovat náklady a maximalizovat přínosy nejen pro náš tým, ale také pro naše klienty."
                ),
                "image": "/static/img/vlk.jpg"
            }
        ]

        context = super().get_context_data(**kwargs)
        context['team_members'] = team_members
        context['total_customers'] = CustomUser.objects.count()
        context['total_events'] = Event.objects.count()
        context['total_orders'] = Order.objects.count()
        context['total_organizations'] = Organization.objects.count()
        return context


class ContactView(View):
    def get(self, request):
        form = ContactForm()
        captcha_key = CaptchaStore.generate_key()
        captcha_image = captcha_image_url(captcha_key)
        return render(request, 'informations/contact.html', {'form': form, "captcha": {
            "key": captcha_key,
            "image": captcha_image,
        }})

    def post(self, request):
        form = ContactForm(request.POST)  # Načtení odeslaných dat z formuláře
        # Ověření, zda uživatel neodeslal formulář v posledních 10 minutách
        last_submitted = request.session.get('last_submission_time')
        if last_submitted:
            # Převeďte uložený čas na datetime objekt
            last_submitted_time = timezone.datetime.fromisoformat(last_submitted)
            time_diff = timezone.now() - last_submitted_time
            if time_diff < timedelta(minutes=10):
                minutes_left = 10 - time_diff.seconds // 60
                new_captcha_key = CaptchaStore.generate_key()
                new_captcha_image = captcha_image_url(new_captcha_key)
                messages.error(request, f"Formulář už byl odeslán. Počkejte ještě {minutes_left} minut(y).")
                return render(request, 'informations/contact.html', {'form': form, "captcha": {
            "key": new_captcha_key,
            "image": new_captcha_image,
        }})

        captcha_key = request.POST.get('captcha_0')
        captcha_value = request.POST.get('captcha_1')

        new_captcha_key = CaptchaStore.generate_key()
        new_captcha_image = captcha_image_url(new_captcha_key)

        # Ověření Captchy
        if not CaptchaStore.objects.filter(response__iexact=captcha_value, hashkey=captcha_key).exists():
            messages.error(request, "Špatně zadaná Captcha. Zkuste to prosím znovu.")
            return render(request, 'informations/contact.html',
                          {'new_message': True, 'form': form, "captcha": {
            "key": new_captcha_key,
            "image": new_captcha_image,
        }})

        if form.is_valid():
            # Odeslání e-mailu adminovi
            subject = f"Nová zprávac od {form.cleaned_data['name']}"
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            html_message = render_to_string('email/contact.html',
                                            {'message': form.cleaned_data['message'], 'name': name, 'email': email})
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            address = settings.CONTACT_EMAIL

            send_mail(subject, plain_message, from_email, [address], html_message=html_message)

            # Uložení času odeslání do session jako ISO formátovaný řetězec pro kompatibilitu s JSON
            request.session['last_submission_time'] = timezone.now().isoformat()

            messages.success(request, "Váš tiket byl úspěšně odeslán.")  # Zobrazení úspěšné zprávy
            return redirect('index')  # Přesměrování zpět na stránku support
        else:
            messages.error(request, "Formulář obsahuje chyby. Zkuste to prosím znovu.")  # Zobrazení chybové zprávy
            return render(request, 'informations/contact.html', {'form': form, "captcha": {
            "key": new_captcha_key,
            "image": new_captcha_image,
        }})


class SupportView(View):
    def get(self, request):
        form = SupportForm()  # Vytvoření prázdného formuláře pro GET request
        return render(request, 'informations/support.html', {'form': form})

    def post(self, request):
        form = SupportForm(request.POST)  # Načtení odeslaných dat z formuláře
        # Ověření, zda uživatel neodeslal formulář v posledních 10 minutách
        last_submitted = request.session.get('last_submission_time')
        if last_submitted:
            # Převeďte uložený čas na datetime objekt
            last_submitted_time = timezone.datetime.fromisoformat(last_submitted)
            time_diff = timezone.now() - last_submitted_time
            if time_diff < timedelta(minutes=10):
                minutes_left = 10 - time_diff.seconds // 60
                messages.error(request, f"Formulář už byl odeslán. Počkejte ještě {minutes_left} minut(y).")
                return render(request, 'informations/support.html', {'form': form})

        if form.is_valid():
            # Odeslání e-mailu adminovi
            subject = f"Nový tiket od {form.cleaned_data['name']}"
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            html_message = render_to_string('email/support_email.html',
                                            {'message': form.cleaned_data['message'], 'name': name, 'email': email})
            plain_message = strip_tags(html_message)
            from_email = settings.EMAIL_HOST_USER
            address = settings.SUPPORT_EMAIL

            send_mail(subject, plain_message, from_email, [address], html_message=html_message)

            # Uložení času odeslání do session jako ISO formátovaný řetězec pro kompatibilitu s JSON
            request.session['last_submission_time'] = timezone.now().isoformat()

            messages.success(request, "Váš tiket byl úspěšně odeslán.")  # Zobrazení úspěšné zprávy
            return redirect('support')  # Přesměrování zpět na stránku support
        else:
            messages.error(request, "Formulář obsahuje chyby. Zkuste to prosím znovu.")  # Zobrazení chybové zprávy
            return render(request, 'informations/support.html', {'form': form})

class CalendarView(View):
    template_name = 'calendar/calendar.html'

    def get(self, request):
        # Získání aktuálního roku a měsíce
        year = int(request.GET.get('year', datetime.now().year))
        month = int(request.GET.get('month', datetime.now().month))

        # Získání prvního a posledního dne měsíce
        first_day = datetime(year, month, 1)
        last_day = first_day + timedelta(days=monthrange(year, month)[1] - 1)

        # Získání všech událostí pro aktuální měsíc
        events = Event.objects.filter(day__range=(first_day, last_day))

        # Rozdělení kalendáře na týdny
        cal = Calendar(firstweekday=0)  # 0 = Pondělí
        weeks = cal.monthdatescalendar(year, month)

        # Struktura kalendáře s událostmi
        calendar_weeks = []
        for week in weeks:
            week_days = []
            for day in week:
                if first_day.date() <= day <= last_day.date():
                    day_events = events.filter(day=day)
                    week_days.append({'day': day, 'events': day_events})
                else:
                    week_days.append(None)  # Dny mimo aktuální měsíc
            calendar_weeks.append(week_days)

        # Slovník měsíců (1 - Leden, 2 - Únor, ...)
        months = {
            1: 'Leden', 2: 'Únor', 3: 'Březen', 4: 'Duben',
            5: 'Květen', 6: 'Červen', 7: 'Červenec', 8: 'Srpen',
            9: 'Září', 10: 'Říjen', 11: 'Listopad', 12: 'Prosinec'
        }

        # Generování dostupných let (např. 2022 - 2029)
        current_year = datetime.now().year
        available_years = list(range(current_year - 5, current_year + 5))

        # Kontext pro šablonu
        context = {
            'calendar_weeks': calendar_weeks,
            'current_year': year,
            'current_month': month,
            'previous_month': (month - 1) if month > 1 else 12,
            'previous_year': year if month > 1 else year - 1,
            'next_month': (month + 1) if month < 12 else 1,
            'next_year': year if month < 12 else year + 1,
            'weekdays': ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"],
            'months': months,  # Přidáno do kontextu
            'available_years': available_years,  # Přidáno do kontextu
        }
        return render(request, self.template_name, context)
