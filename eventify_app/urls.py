from tkinter.font import names

from django.conf.urls.static import static
from django.urls import path, include
from django.contrib import admin

from eventify import settings
from .views import index, purchase_ticket, EventManagerView, EventCreateView, EventDeleteView, EventDetailView, \
    EventUpdateView, UserProfileView, MyProfileView, UserProfileEditView, CartView, RemoveItemView, ClearCartView, \
    CartInformationsView, \
    CartPaymentView, CartConfirmationView, TermsOfUseView, SupportView, PrivacyPolicy, Faq, ContactView, \
    AboutUs, EditTicketView, DeleteTicketView, AddTicketView, EventsListView, CalendarView, MyEventsListView, \
    generate_ticket_pdf

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
    path('eventmanager/editticket/<int:pk>/', EditTicketView.as_view(), name='edit_ticket'),
    path('eventmanager/delete_ticket/<int:ticket_id>/', DeleteTicketView.as_view(), name='delete_ticket'),
    path('eventmanager/add_ticket/<int:event_pk>/', AddTicketView.as_view(), name='add_ticket'),
    path('eventmanager/delete/<int:pk>/', EventDeleteView.as_view(), name='delete_event'),
    path('events_list/', EventsListView.as_view(), name='events_list'),
    path('my_tickets/', MyEventsListView.as_view(), name='my_tickets'),
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
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('order/<int:order_id>/pdf/', generate_ticket_pdf, name='generate_ticket_pdf'),
    path('captcha/', include('captcha.urls')),
]

if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)