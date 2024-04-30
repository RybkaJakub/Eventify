from django.urls import path
# Import pohledů pro zobrazení galerie autorů a detailu autora
from .views import index

urlpatterns = [
    # URL adresa pro zobrazení domovské stránky
    path('', index, name='index')
]