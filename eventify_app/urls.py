from tkinter.font import names

from django.urls import path, include

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from .views import index, purchase_ticket, EventManagerView, EventCreateView, EventDeleteView, EventDetailView, \
    EventUpdateView, MyEventsListView, delete_ticket_type, \
    UserProfileView, MyProfileView, UserProfileEditView, CartView, RemoveItemView, ClearCartView, CartInformationsView, \
    CartPaymentView, CartConfirmationView, events_list, TermsOfUseView, SupportView, PrivacyPolicy, Faq, ContactView, \
    AboutUs

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
    path('events_list/', events_list, name='events_list'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/remove/<int:item_id>/', RemoveItemView.as_view(), name='remove_item'),
    path('cart/clear', ClearCartView.as_view(), name='clear_cart'),
    path('cart/informations/', CartInformationsView.as_view(), name='cart_informations'),
    path('cart/payment/', CartPaymentView.as_view(), name='cart_payment'),
    path('cart/confirmation/', CartConfirmationView.as_view(), name='cart_confirmation'),
    path('event_detail/<int:pk>/', EventDetailView.as_view(), name='event_detail'),
    path('purchase_ticket/<int:pk>/', purchase_ticket, name='purchase_ticket'),
    path('terms/', TermsOfUseView.as_view(), name='terms'),
    path('privacy/', PrivacyPolicy.as_view(), name='privacy'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('faq/', Faq.as_view(), name='faq'),
    path('about_us/', AboutUs.as_view(), name='aboutus'),
    path('support/', SupportView.as_view(), name='support'),
]
