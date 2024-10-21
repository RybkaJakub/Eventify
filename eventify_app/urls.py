from django.urls import path, include

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from .views import index, purchase_ticket, EventManagerView, EventCreateView, EventDeleteView, EventDetailView, \
    EventUpdateView, MyEventsListView, delete_ticket_type, \
    UserProfileView, MyProfileView, UserProfileEditView

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin.site.urls),
    path('account/', include('allauth.urls')),
    path('myprofile/', MyProfileView.as_view(), name='myprofile'),
    path('editprofile/', UserProfileEditView.as_view(), name='editprofile'),
    path('profile/<int:pk>', UserProfileView.as_view(), name='profile'),
    path('eventmanager/', EventManagerView.as_view(), name='event_manager'),
    path('eventmanager/create/', EventCreateView.as_view(), name='create_event'),
    path('eventmanager/edit/<int:pk>/', EventUpdateView.as_view(), name='edit_event'),
    path('eventmanager/delete-ticke_type/<int:pk>/', delete_ticket_type, name='delete_ticket_type'),
    path('eventmanager/delete/<int:pk>/', EventDeleteView.as_view(), name='delete_event'),
    path('my_events_list/', MyEventsListView.as_view(), name='my_events_list'),
    path('event_detail/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('purchase_ticket/<int:pk>', purchase_ticket, name='purchase_ticket'),
]
