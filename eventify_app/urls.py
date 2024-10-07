from django.urls import path, include

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from .views import index, purchase_ticket, EventManagerView, EventCreateView, EventDeleteView, EventDetailView, \
    EventUpdateView, CustomLoginView, CustomLogoutView, SignUpView, MyEventsListView, delete_ticket_type

urlpatterns = [
    # URL adresa pro zobrazení domovské stránky
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('eventmanager/', EventManagerView.as_view(), name='event_manager'),
    path('eventmanager/create/', EventCreateView.as_view(), name='create_event'),
    path('eventmanager/edit/<int:pk>/', EventUpdateView.as_view(), name='edit_event'),
path('eventmanager/delete-ticke_type/<int:pk>/', delete_ticket_type, name='delete_ticket_type'),
    path('eventmanager/delete/<int:pk>/', EventDeleteView.as_view(), name='delete_event'),
    path('my_events_list/', MyEventsListView.as_view(), name='my_events_list'),
    path('event_detail/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('event/<int:event_id>/purchase/', purchase_ticket, name='purchase_ticket'),
    path('accounts/login/', CustomLoginView.as_view(), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path('accounts/signup/', SignUpView.as_view(), name='signup'),
]
