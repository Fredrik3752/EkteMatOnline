# Ekte Mat Online

INFO212 – Obligatorisk innlevering 4. En første versjon av bestillingsløsningen
for den fiktive cateringbedriften Ekte Mat AS i Bergen: kundeside og
administrasjonspanel, bygget med Flask, Jinja2 og SQLite etter MVC-mønsteret.

> Alle personer, bedrifter og data i prosjektet er syntetiske.

## Krav

- Python 3.9 eller nyere
- Git

## Installere

```bash
git clone https://github.com/Fredrik3752/EkteMatOnline.git
cd EkteMatOnline
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # sett en egen SECRET_KEY
```

## Database

Databasen (`instance/ektemat.db`) opprettes automatisk ved første oppstart.
Slik nullstiller du den:

```bash
flask --app app init-db
```

Seed-skript med syntetiske matretter, en administrator og testkunder kommer i fase 2.

## Kjøre

```bash
flask --app app run --debug
```

Åpne http://127.0.0.1:5000.

## Teste

```bash
pytest
```

## Struktur (MVC)

```
app/
  models/                domeneklasser
    repositories/        all datatilgang (SQLite nå, Neo4j i oblig 5)
  controllers/           Flask-blueprints
  templates/             Jinja2-views
  static/                CSS, JS, bilder
tests/                   pytest
docs/plans/              plan for hver fase/funksjon
```
