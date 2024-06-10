from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views import View

from .models import Event, UserEventRegistration
from .forms import EventForm, CustomAuthenticationForm, LogoutForm, SignUpForm
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.views import LoginView


def index(request):
    registered_events = []
    divider_rendered = False

    now = timezone.now()
    upcoming_events = Event.objects.filter(datetime__gt=now).order_by('datetime')

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

        return context


class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'create_event.html'
    permission_required = 'eventify_app.add_event'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('event_detail', kwargs={'pk': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_manager_edit.html'
    permission_required = 'eventify_app.change_event'
    success_url = '/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['event'] = self.object
        return context

class EventDeleteView(LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_manager_delete.html'
    context_object_name = 'event'
    success_url = '/'
    permission_required = 'eventify_app.delete_event'

    def test_func(self):
        return self.request.user

class EventDetailView(DetailView):
    model = Event
    template_name = 'event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        seats_taken = UserEventRegistration.objects.filter(event=self.object).count()
        seats_left = self.object.seats - seats_taken
        context['seatsLeft'] = seats_left
        context['isAdmin'] = False
        context['registeredUsers'] = [registration.user for registration in
                                      UserEventRegistration.objects.filter(event=self.object)]
        if self.object.organization == self.request.user.organization:
            context['userOrganization'] = True
        else:
            context['userOrganization'] = False
        if self.request.user.is_authenticated:

            for group in self.request.user.groups.all():
                if group.name == "editor" or group.name == "admin":
                    context['isAdmin'] = True
                    break
        if self.request.user.is_authenticated:
            # Zkontroluje, zda je uživatel registrován na daný event
            context['registered'] = UserEventRegistration.objects.filter(
                user=self.request.user,
                event=self.object
            ).exists()
        else:
            context['registered'] = False
        return context

class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = 'login.html'

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

@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    # Zkontroluje, zda je uživatel již zaregistrován na tuto událost
    existing_registration = UserEventRegistration.objects.filter(user=request.user, event=event).exists()
    if existing_registration:
        messages.warning(request, f'Již jste registrováni na event "{event.name}".')
    else:
        # Vytvoří nový záznam registrace
        UserEventRegistration.objects.create(user=request.user, event=event)
        messages.success(request, f'Byli jste úspěšně zaregistrováni na event "{event.name}".')
    return redirect('event_detail', pk=event_id)
