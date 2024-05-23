from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from .models import Event, UserEventRegistration
from .forms import EventForm
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView


def index(request):
    registered_events = []
    divider_rendered = False

    now = timezone.now()
    upcoming_events = Event.objects.filter(datetime__gt=now).order_by('datetime')

    if request.user.is_authenticated:

        registered_events = UserEventRegistration.objects.filter(user=request.user)

        for group in request.user.groups.all():
            if group.name == "eventer" or group.name == "admin":
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
    context_object_name = 'events'
    permission_required = 'eventify_app.change_event'

class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'create_event.html'
    permission_required = 'eventify_app.add_event'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class EventUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'edit_event.html'
    permission_required = 'eventify_app.change_event'

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

@login_required
def register_for_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    registration, created = UserEventRegistration.objects.get_or_create(event=event, user=request.user)
    if created:
        messages.success(request, f'Byli jste úspěšně zaregistrováni na event "{event.name}".')
    else:
        messages.warning(request, f'Již jste registrováni na event "{event.name}".')
    return redirect('event_detail', event_id=event_id)
