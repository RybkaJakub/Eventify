from django.urls import path

from django.contrib import admin
from .views import index, register_for_event, EventManagerView, EventCreateView, EventDeleteView, EventDetailView, EventUpdateView, EventForm, UserEventRegistration


urlpatterns = [
    # URL adresa pro zobrazení domovské stránky
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('eventmanager/', EventManagerView.as_view(), name='event_manager'),
    path('eventmanager/create/', EventCreateView.as_view(), name='create_event'),
    path('eventmanager/edit/<int:pk>/', EventUpdateView.as_view(), name='edit_event'),
    path('eventmanager/delete/<int:pk>/', EventDeleteView.as_view(), name='delete_event'),
    path('event_detail/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event_detail/<int:event_id>/register/', register_for_event, name='register_for_event'),
]
