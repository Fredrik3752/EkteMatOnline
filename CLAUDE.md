# CLAUDE.md – Ekte Mat Online

## Hva systemet er
Bestillings- og cateringløsning for den fiktive Bergen-bedriften Ekte Mat AS
(INFO212 oblig 4). Kundeside (meny per arrangement, handlekurv, bestilling, mine
ordrer, spørsmål) og administrasjonspanel (matretter, bilder, ordrer, svar på
spørsmål). Krav: A1–A4 og C1–C5 i oppgaveteksten; status per fase i `docs/plans/`.
Ferdig: innlogging (fase 3), A1 + C1 (fase 4), C2 handlekurv + C3 bestilling (fase 5). Gjenstår: C4, C5, A2–A4.

## Stack
Python 3.9+, Flask 3.1, Jinja2, SQLite (`sqlite3`), pytest. Ingen betalte API-er.

## MVC-oppsett
- `app/models/` – domeneklasser (dataclasses) med forretningsregler: `FoodItem`, `Order` (tilstandsmaskin for `OrderStatus`), `PaymentStatus`, `GuestGroup`, `Question`, `User`. Regelbrudd gir `ValidationError` / `InvalidStatusTransition`.
- `app/models/repositories/` – **eneste** sted som rører SQLite (`database.py`, `schema.sql`, `*_repository.py`). Skal kunne byttes mot Neo4j i oblig 5.
- `app/controllers/` – Flask-blueprints `shop` (meny), `cart` (handlekurv i session), `checkout` (bestilling), `account` (registrer/logg inn/ut) og `admin` (`/admin`). Kaller repositories, rendrer maler. `auth.py` gir `g.user`, `@login_required` og `@admin_required`; `csrf.py` sjekker token på alle POST.
- `app/templates/` – Jinja2-views; `app/static/` – CSS/JS/bilder.

## Kommandoer
```bash
source .venv/bin/activate
pip install -r requirements.txt
flask --app app seed         # nullstiller og fyller inn syntetiske testdata
flask --app app init-db      # nullstiller til tom database
flask --app app run --debug  # http://127.0.0.1:5000
pytest
```

## Regler
- Ikke importer `sqlite3` eller skriv SQL utenfor `app/models/repositories/`.
- Repositories returnerer domeneobjekter, ikke `sqlite3.Row`. Statusendringer går via `Order.change_status()`, aldri direkte i SQL.
- Seed-data (`app/seed.py`) er oppdiktet og bruker `.test`-domener; passord leses fra `.env`.
- Handlekurven ligger i session som `{"<item_id>": antall}`; `log_in()` beholder den. Regler for kurven ligger i `app/models/cart.py`.
- Priser lagres i øre (heltall). Allergier lagres per gjestegruppe, ikke per navngitt gjest.
- Kun syntetiske data. Ikke les, kopier eller commit noe fra `EkteMat_project_inbox 2/` eller oppgave-PDF-en.
- Ingen hemmeligheter i Git: bruk `.env` (ignorert), dokumenter nøkler i `.env.example`.
- Større funksjoner planlegges først i plan mode; planen lagres i `docs/plans/NN-navn.md` før koding.
- Alle skjemaer med POST har `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`. Admin-ruter har `@admin_required`.
- Tester bruker `post()`/`login()` fra `tests/conftest.py` (setter CSRF-token).
- Ny funksjonalitet får tester i `tests/`; `pytest` skal være grønn før commit.
- Kode og kommentarer på engelsk, brukergrensesnitt på norsk.
