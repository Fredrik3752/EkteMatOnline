# CLAUDE.md – Ekte Mat Online

## Hva systemet er
Bestillings- og cateringløsning for den fiktive Bergen-bedriften Ekte Mat AS
(INFO212 oblig 4). Kundeside (meny per arrangement, handlekurv, bestilling, mine
ordrer, spørsmål) og administrasjonspanel (matretter, bilder, ordrer, svar på
spørsmål). Krav: A1–A4 og C1–C5 i oppgaveteksten; status per fase i `docs/plans/`.

## Stack
Python 3.9+, Flask 3.1, Jinja2, SQLite (`sqlite3`), pytest. Ingen betalte API-er.

## MVC-oppsett
- `app/models/` – domeneklasser (dataclasses).
- `app/models/repositories/` – **eneste** sted som rører SQLite (`database.py`, `schema.sql`, `*_repository.py`). Skal kunne byttes mot Neo4j i oblig 5.
- `app/controllers/` – Flask-blueprints (`shop`, senere `account`, `admin`). Kaller repositories, rendrer maler.
- `app/templates/` – Jinja2-views; `app/static/` – CSS/JS/bilder.

## Kommandoer
```bash
source .venv/bin/activate
pip install -r requirements.txt
flask --app app init-db      # nullstiller databasen
flask --app app run --debug  # http://127.0.0.1:5000
pytest
```

## Regler
- Ikke importer `sqlite3` eller skriv SQL utenfor `app/models/repositories/`.
- Repositories returnerer domeneobjekter, ikke `sqlite3.Row`.
- Priser lagres i øre (heltall). Allergier lagres per gjestegruppe, ikke per navngitt gjest.
- Kun syntetiske data. Ikke les, kopier eller commit noe fra `EkteMat_project_inbox 2/` eller oppgave-PDF-en.
- Ingen hemmeligheter i Git: bruk `.env` (ignorert), dokumenter nøkler i `.env.example`.
- Større funksjoner planlegges først i plan mode; planen lagres i `docs/plans/NN-navn.md` før koding.
- Ny funksjonalitet får tester i `tests/`; `pytest` skal være grønn før commit.
- Kode og kommentarer på engelsk, brukergrensesnitt på norsk.
