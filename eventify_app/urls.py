from tkinter.font import names

from django.urls import path, include

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from .views import index, purchase_ticket, EventManagerView, EventCreateView, EventDeleteView, EventDetailView, \
    EventUpdateView, MyEventsListView, delete_ticket_type, \
    UserProfileView, MyProfileView, UserProfileEditView, CartView, RemoveItemView, ClearCartView, CartInformationsView, \
    CartPaymentView, CartConfirmationView, event_list

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
    path('my_events_list/', event_list, name='my_events_list'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/remove/<int:item_id>/', RemoveItemView.as_view(), name='remove_item'),
    path('cart/clear', ClearCartView.as_view(), name='clear_cart'),
    path('cart/informations/', CartInformationsView.as_view(), name='cart_informations'),
    path('cart/payment/', CartPaymentView.as_view(), name='cart_payment'),
    path('cart/confirmation/', CartConfirmationView.as_view(), name='cart_confirmation'),
    path('event_detail/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('purchase_ticket/<int:pk>/', purchase_ticket, name='purchase_ticket'),
]
