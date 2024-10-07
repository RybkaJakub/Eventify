
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse
from django.views import View

from .models import Event, TicketType, TicketPurchase
from .forms import EventForm, CustomAuthenticationForm, LogoutForm, SignUpForm, TicketTypeFormSet
from django.utils import timezone
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView
from django.urls import resolve
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

        """registered_events = UserEventRegistration.objects.filter(user=request.user)"""

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
            ticket_type.save()

class EventCreateView(EventInline, CreateView, LoginRequiredMixin, PermissionRequiredMixin):

     def get_context_data(self, **kwargs):
         ctx = super(EventCreateView, self).get_context_data(**kwargs)
         ctx['named_formsets'] = self.get_named_formsets()
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

class EventUpdateView(EventInline, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    def get_context_data(self, **kwargs):
        ctx = super(EventUpdateView, self).get_context_data(**kwargs)
        ctx['named_formsets'] = self.get_named_formsets()
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
        if self.request.user.is_authenticated:

            for group in self.request.user.groups.all():
                if group.name == "editor" or group.name == "admin":
                    context['isAdmin'] = True
                    break
        if self.request.user.is_authenticated:
            context['registered'] = TicketPurchase.objects.filter(
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

            registered_events = TicketPurchase.objects.filter(user=user).values_list('event', flat=True)
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

        ticket_type = get_object_or_404(TicketType, id=ticket_type_id)

        total_amount = ticket_type.price * quantity

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