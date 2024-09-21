## Instalace

1. Klonujte tento repozitář:  
   `git clone https://github.com/YourUsername/Eventify.git`
2. Vytvořte a aktivujte virtuální prostředí:  
   `python -m venv venv`  
   `source venv/bin/activate` (Linux/macOS)  
   `venv\Scripts\activate` (Windows)
3. Nainstalujte závislosti:  
   `pip install -r requirements.txt`
4. Nastavte databázi v `settings.py` pro PostgreSQL.
5. Proveďte migrace databáze:  
   `python manage.py migrate`
6. Spusťte server:  
   `python manage.py runserver`