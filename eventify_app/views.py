from lib2to3.fixes.fix_input import context

from allauth.account.views import SignupView
from django.conf import settings
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from django.utils.html import strip_tags
from django.views import View

from .models import Event, TicketType, TicketPurchase, Address, CustomUser, Cart, DeliveryAddress, PaymentMethod
from allauth.socialaccount.models import SocialAccount
from .forms import UserProfileEditForm, DeliveryAddressForm, CustomUserForm, PaymentMethodForm
from django.utils import timezone
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.urls import resolve

import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMessage, send_mail

import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMessage

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
    divider_rendered = False
    profile_picture = ''
    has_picture = False

    now = timezone.now()
    upcoming_events = Event.objects.all() # Use prefetch_related for reverse relationships

    if request.user.is_authenticated:
        registered_events = TicketPurchase.objects.filter(user=request.user).distinct('event')

        social_accounts = SocialAccount.objects.filter(user=request.user)
        profile_picture = UserProfileView.get_user_profile_picture(request, social_accounts)
        if profile_picture:
            has_picture = True
        for group in request.user.groups.all():
            if group.name == "editor" or group.name == "admin":
                divider_rendered = True
                break



    context = {
        'divider_rendered': divider_rendered,
        'upcoming_events': upcoming_events,
        'registered_events': registered_events,
        'profile_picture': profile_picture,
        'has_picture': has_picture,
        'user': request.user
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

        profile_picture = UserProfileView.get_user_profile_picture(self.request, SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True

        context['organization'] = organization
        context['in_organization'] = in_organization
        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture
        context['events'] = Event.objects.filter(organization=organization)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name

        return context

from django.shortcuts import render
from django.urls import reverse_lazy
from django.forms import inlineformset_factory
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Event, TicketType
from .forms import EventForm, TicketTypeFormSet

class EventInline():
    form_class = EventForm
    model = Event
    template_name = "create_event.html"

    def form_valid(self, form):
        named_formsets = self.get_named_formsets()
        if not all((x.is_valid() for x in named_formsets.values())):
            return self.render_to_response(self.get_context_data(form=form))

        form.instance.created_by = self.request.user
        self.object = form.save()

        for name, formset in named_formsets.items():
            formset_save_func = getattr(self, 'formset_{0}_valid'.format(name), None)
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

class EventCreateView(EventInline, CreateView, LoginRequiredMixin, PermissionRequiredMixin):

     def get_context_data(self, **kwargs):
         ctx = super(EventCreateView, self).get_context_data(**kwargs)
         ctx['named_formsets'] = self.get_named_formsets()
         has_picture = False
         profile_picture = UserProfileView.get_user_profile_picture(self.request, SocialAccount.objects.filter(user=self.request.user))
         if profile_picture:
             has_picture = True
         ctx['profile_picture'] = profile_picture
         ctx['has_picture'] = has_picture
         return ctx

     def get_named_formsets(self):
         if self.request.method == 'GET':
             return {
                 'ticket_types': TicketTypeFormSet(prefix='ticket_types')
             }
         else:
             return {
                 'ticket_types': TicketTypeFormSet(self.request.POST or None, self.request.FILES or None
                                                   ,prefix='ticket_types')
             }

class EventUpdateView(EventInline, LoginRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super(EventUpdateView, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True
        ctx['has_picture'] = has_picture
        ctx['profile_picture'] = profile_picture
        return ctx

    def get_named_formsets(self):
        return {
            'ticket_types': TicketTypeFormSet(self.request.POST or None, self.request.FILES or None,
                                              prefix='ticket_types', instance=self.object)
        }

def delete_ticket_type(request, pk):
    try:
        ticket_type = TicketType.objects.get(id=pk)
    except TicketType.DoesNotExist:
        messages.success(
            request, 'Objekt neexistuje.'
        )
    ticket_type.delete()
    messages.success(
        request, 'Vstupenka byla úspěšně smazána.'
    )
    return redirect('edit_event', pk=ticket_type.event.id)

from django.shortcuts import get_object_or_404


class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_manager_delete.html'
    context_object_name = 'event'
    success_url = '/'
    permission_required = 'eventify_app.delete_event'

    def test_func(self):
        return self.request.user

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
    template_name = 'event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['isAdmin'] = False
        context['userOrganization'] = False
        context['purchasedTickets'] = TicketPurchase.objects.filter(event=self.object)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        context['ticket_types'] = TicketType.objects.filter(event=self.object)

        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True
        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture

        auth = self.request.user.is_authenticated
        context['isAuth'] = auth

        if auth:
            # Pouze pro přihlášené uživatele
            context['userTickets'] = TicketPurchase.objects.filter(
                user=self.request.user,
                event=self.object
            )
            context['registered'] = TicketPurchase.objects.filter(
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

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress
from .models import Address  # Import your Address model

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
        viewed_picture = UserProfileView.get_user_profile_picture(self.request, SocialAccount.objects.filter(user=vieweduser))
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request, SocialAccount.objects.filter(user=self.request.user))
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
    model = Event
    template_name = 'events/events_list.html'
    context_object_name = 'events'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        if (self.request.user.is_authenticated):
            user = self.request.user

            registered_events = TicketPurchase.objects.filter(user=user).values_list('event', flat=True)
            context['events'] = Event.objects.filter(id__in=registered_events)
            context['isAuth'] = True
        else:
            context['events'] = []
            context['isAuth'] = False
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
                    messages.error(request, f'Nemůžete si objednat více než {item.ticket_type.left} vstupenek pro {item.ticket_type.name}.')
                    return redirect('cart')
                item.quantity = quantity
                item.total_amount = item.ticket_type.price * quantity
                item.save()

        messages.success(request, 'Košík byl úspěšně aktualizován.')
        return redirect('cart')


from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from allauth.socialaccount.models import SocialAccount
from .forms import CustomUserForm, DeliveryAddressForm

class CartInformationsView(LoginRequiredMixin, TemplateView):
    """Opravit chyby s tím že když uživatel zadá neplatnou hodnotu tak se neuloží např číslo popisné 632/7"""
    template_name = "account/cart_informations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['user'] = user
        delivery_address = DeliveryAddress.objects.filter(user=user).first()
        context['delivery_address'] = delivery_address
        context['user_form'] = CustomUserForm(instance=user)
        context['address_form'] = DeliveryAddressForm(instance=DeliveryAddress.objects.filter(user=user).first())


        # Kontrola pro profilový obrázek
        has_picture = False
        profile_picture = UserProfileView.get_user_profile_picture(self.request,
                                                                   SocialAccount.objects.filter(user=self.request.user))
        if profile_picture:
            has_picture = True

        context['has_picture'] = has_picture
        context['profile_picture'] = profile_picture

        return context

    def post(self, request, *args, **kwargs):
        user_form = CustomUserForm(request.POST, instance=request.user)
        address_form = DeliveryAddressForm(request.POST, instance=DeliveryAddress.objects.filter(user=request.user).first())

        if user_form.is_valid() and address_form.is_valid():
            user_form.save()
            address_form.instance.user = request.user
            address_form.save()
            messages.success(request, 'Vaše informace byly úspěšně aktualizovány.')
            return redirect('cart_informations')
        else:
            messages.error(request, 'Chyba při aktualizaci informací. Zkontrolujte zadání.')

        # V případě neplatného formuláře znovu načti formuláře s chybami
        context = self.get_context_data()
        context['user_form'] = user_form  # Zahrnout formuláře s chybami
        context['address_form'] = address_form
        return render(request, self.template_name, context)


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
        # Získání nebo vytvoření metody platby, pokud neexistuje
        payment_method, created = PaymentMethod.objects.get_or_create(user=request.user)
        payment_form = PaymentMethodForm(request.POST, instance=payment_method)

        if payment_form.is_valid():
            payment_form.save()
            messages.success(request, 'Vaše informace byly úspěšně aktualizovány.')
            return redirect('cart_payment')
        else:
            messages.error(request, 'Chyba při aktualizaci informací. Zkontrolujte zadání.')

        # V případě neplatného formuláře znovu načítání kontextu
        context = self.get_context_data()
        context['payment_form'] = payment_form
        return render(request, self.template_name, context)

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

    def post(self, request, *args, **kwargs):
        address = "jakubekrybka@gmail.com"
        subject = "Objednávka vstupenek"
        message = ("Dobrý den,\n\n"
                   "Děkujeme za vaši objednávku vstupenek. V příloze naleznete detaily objednávky.\n\n"
                   "S pozdravem,\n"
                   "Tým Eventify")
        tickets = Cart.objects.filter(user=request.user)

        if address and subject and message:
            subject = 'Potvrzení nákupu vstupenek - Eventify'
            html_message = render_to_string('email/email.html',
                                            {'tickets': tickets, 'user_name': 'Jakub Rybka'})
            plain_message = strip_tags(html_message)
            from_email = 'ev3ntify@gmail.com'

            send_mail(subject, plain_message, from_email, [address], html_message=html_message)
        return redirect('index')

class RemoveItemView(LoginRequiredMixin, View):
    def post(self, request, item_id):
        item = get_object_or_404(Cart, id=item_id, user=request.user)
        item.delete()
        return redirect('cart')

class ClearCartView(LoginRequiredMixin, View):
    def post(self, request):
        Cart.objects.filter(user=request.user).delete()
        return redirect('cart')  # Přesměrování zpět na stránku s košíkem