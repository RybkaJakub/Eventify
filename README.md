
# Maturitní projekt - Eventify

![Version](https://img.shields.io/badge/Verze-1.0-green.svg?logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%3D...)
[![Developer](https://img.shields.io/badge/Developer-Jakub_Rybka-orange)](https://github.com/RybkaJakub/Eventify)
[![Framework](https://img.shields.io/badge/Framework-Django-purple)](https://www.djangoproject.com)
[![Database](https://img.shields.io/badge/Datab%C3%A1ze-PostreSQL-blue)](https://www.postgresql.org)
[![Frontend](https://img.shields.io/badge/Frontend-Tailwind_CSS-red)](https://tailwindcss.com/)

## Popis projektu

**Eventify** je webová aplikace napsaná v Djangu, zaměřená na moderní a efektivní organizaci různých typů událostí, jako jsou konference, workshopy, festivaly nebo sportovní akce. Cílem je poskytnout uživatelům přehled o nadcházejících událostech, usnadnit organizátorům jejich správu a umožnit účastníkům jednoduchý proces registrace.

Aplikace je rozdělena do částí pro **organizátory** a **účastníky**. Organizátoři mohou spravovat události a sledovat registrace, zatímco účastníci mají možnost prohlížet si nabídky událostí, filtrovat je podle svých zájmů, rezervovat si místa a propojit se s dalšími účastníky.

### Funkce

- **Domovská stránka**: Přehled aktuálních a doporučených událostí s možností vytvoření nové události.
- **Prohlížení událostí**: Uživatelé mohou filtrovat události podle data, tématu nebo lokace a zobrazit podrobné informace o programu, místě konání a ceně vstupenek.
- **Registrace na události**: Rezervace míst na událostech pomocí jednoduchého online formuláře.
- **Správa událostí**: Organizátoři mohou snadno přidávat, upravovat a mazat informace o svých událostech, sledovat registrace a komunikovat s účastníky.
- **OAuth 2.0** pro bezpečné přihlášení pomocí externích účtů jako je Google, GitHub nebo Discord.

### Budoucí vylepšení

- **Platební brána**: Integrovaná možnost platby za vstupenky přímo přes aplikaci.
- **Rezervace sedadel**: Možnost výběru konkrétních sedadel na událostech.
- **Komunikace s účastníky**: Systém e-mailových notifikací, diskusních fór a chatovací funkce pro lepší interakci mezi organizátory a účastníky.
- **Personalizovaná doporučení**: Funkce pro doporučení událostí na základě uživatelských preferencí a historie registrací.

## Technologie

| Technologie       | Popis                                                                               |
|-------------------|-------------------------------------------------------------------------------------|
| **Backend**       | Django – výkonný framework pro rychlý vývoj a správu webových aplikací.             |
| **Databáze**      | PostgreSQL – relační databáze optimalizovaná pro vysoký výkon a komplexní dotazy.   |
| **Frontend**      | Tailwind CSS – utility-first CSS framework pro tvorbu responzivního designu.        |
| **Autentizace**   | Django AllAuth – podpora OAuth a dalších metod pro bezpečné přihlašování uživatelů. |
| **Deployment**    | Docker – usnadňuje balení a nasazování aplikace.                                    |
| **Hosting**       | xxx                                                                                 |

## Instalace a spuštění

Chcete-li spustit projekt lokálně, postupujte následovně:

1. **Klonujte tento repozitář**:
   ```bash
   git clone https://github.com/RybkaJakub/Eventify.git
   cd Eventify
   ```

2. **Vytvořte virtuální prostředí** a aktivujte jej:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Nainstalujte požadované balíčky**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Vytvořte databázi**:
   Nastavte připojení k PostgreSQL a aplikujte migrace:
   ```bash
   python manage.py migrate
   ```

5. **Spusťte vývojový server**:
   ```bash
   python manage.py runserver
   ```

## Použité zdroje

- **[Django Documentation](https://docs.djangoproject.com/)**: Kompletní dokumentace k Djangu, obsahuje informace o instalaci, nastavení a funkcích frameworku.
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)**: Dokumentace k PostgreSQL pro optimální správu databáze.
- **[Tailwind CSS Guide](https://tailwindcss.com/docs/)**: Průvodce využitím Tailwind CSS pro styling frontendové části aplikace.
- **[Django AllAuth Documentation](https://docs.allauth.org/en/latest/)**: Dokumentace pro OAuth a další možnosti autentizace.
- **[Docker Docs](https://docs.docker.com/)**: Oficiální dokumentace k Dockeru, obsahující postupy pro vytváření kontejnerů a nasazování aplikací.

---
