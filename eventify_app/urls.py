from django.urls import path

from django.contrib import admin
# Import pohledů pro zobrazení galerie autorů a detailu autora
from .views import index

urlpatterns = [
    # URL adresa pro zobrazení domovské stránky
    path('', index, name='index'),
    path('admin/', admin.site.urls),


]