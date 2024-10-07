
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views import View

from .models import Event, UserEventRegistration, TicketPurchase
from .forms import EventForm, CustomAuthenticationForm, LogoutForm, SignUpForm, TicketTypeFormSet, TicketTypeForm
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView
from django.urls import resolve
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import logging
import uuid


def index(request):
    registered_events = []
    divider_rendered = False

    now = timezone.now()
    """upcoming_events = Event.objects.filter(
        Q(day__gt=now.date()) | (Q(day=now.date()) & Q(start_time__gt=now.time()))
    ).order_by('day', 'start_time')"""
    upcoming_events = Event.objects.all()
    if request.user.is_authenticated:

        registered_events = UserEventRegistration.objects.filter(user=request.user)

        for group in request.user.groups.all():
            if group.name == "editor" or group.name == "admin":
                divider_rendered = True
                break

    context = {
        'divider_rendered': divider_rendered,
        'upcoming_events': upcoming_events,
        'registered_events': registered_events
    }
    return render(request, 'index.html', context=context)


class EventManagerView(PermissionRequiredMixin, ListView):
    model = Event
    template_name = 'events/event_manager.html'
    permission_required = 'eventify_app.change_event'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        organization = user.organization

        in_organization = True if organization else False

        context['organization'] = organization
        context['in_organization'] = in_organization
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


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'create_event.html'
    success_url = reverse_lazy('event_manager')

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        ticket_formset = TicketTypeFormSet(self.request.POST)

        if ticket_formset.is_valid():
            response = super().form_valid(form)

            tickets = ticket_formset.save(commit=False)
            for ticket in tickets:
                ticket.event = self.object
                ticket.save()

            return response
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unique_id'] = str(uuid.uuid4())

        if self.request.POST:
            context['ticket_formset'] = TicketTypeFormSet(self.request.POST)
        else:
            context['ticket_formset'] = TicketTypeFormSet(queryset=TicketType.objects.none())

        return context

from django.http import HttpResponse
from django.template.loader import render_to_string


def add_ticket_row(request):
    form = TicketTypeForm()
    unique_id = str(uuid.uuid4())
    rendered_form = render_to_string('partials/ticket.html', {'form': form, 'unique_id': unique_id}, request=request)
    return HttpResponse(rendered_form)

logger = logging.getLogger(__name__)
from django.shortcuts import get_object_or_404

class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_manager_edit.html'
    permission_required = 'eventify_app.change_event'
    success_url = '/'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.object
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        return context


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
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['isAdmin'] = False
        context['userOrganization'] = False
        context['registeredUsers'] = [registration.user for registration in
                                      UserEventRegistration.objects.filter(event=self.object)]
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        context['ticket_types'] = TicketType.objects.filter(event=self.object)
        if self.request.user.is_authenticated:

            for group in self.request.user.groups.all():
                if group.name == "editor" or group.name == "admin":
                    context['isAdmin'] = True
                    break
        if self.request.user.is_authenticated:
            context['registered'] = UserEventRegistration.objects.filter(
                user=self.request.user,
                event=self.object
            ).exists()
            if self.object.organization == self.request.user.organization:
                context['userOrganization'] = True
        else:
            context['registered'] = False
        return context


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        return context


class CustomLogoutView(View):
    template_name = 'logged_out.html'
    form_class = LogoutForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            logout(request)
            return HttpResponseRedirect(reverse('index'))
        return render(request, self.template_name, {'form': form})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

    def form_valid(self, form):
        password = form.cleaned_data.get('password1')

        user = form.save(commit=False)
        user.set_password(password)
        user.save()

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name
        return context


class MyEventsListView(ListView):
    model = Event
    template_name = 'events/events_list.html'
    context_object_name = 'events'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        if (self.request.user.is_authenticated):
            user = self.request.user

            # Najít eventy, na které je uživatel registrován
            registered_events = UserEventRegistration.objects.filter(user=user).values_list('event', flat=True)
            context['events'] = Event.objects.filter(id__in=registered_events)
            context['isAuth'] = True
        else:
            context['events'] = []
            context['isAuth'] = False
        current_url_name = resolve(self.request.path_info).url_name
        context['current_url'] = current_url_name

        return context

@login_required
def purchase_ticket(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        ticket_type_id = request.POST.get('ticket_type')
        quantity = int(request.POST.get('quantity'))

        # Získání typu vstupenky
        ticket_type = get_object_or_404(TicketType, id=ticket_type_id)

        # Výpočet celkové částky
        total_amount = ticket_type.price * quantity

        # Vytvoření záznamu o nákupu
        TicketPurchase.objects.create(
            user=request.user,
            event=event,
            ticket_type=ticket_type,
            quantity=quantity,
            total_amount=total_amount
        )

        messages.success(request, f'Úspěšně jste zakoupili {quantity} vstupenek na event "{event.name}".')
        return redirect('event_detail', pk=event_id)

    return redirect('event_detail', pk=event_id)