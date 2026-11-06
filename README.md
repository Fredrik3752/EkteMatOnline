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
Fyll den med syntetiske testdata (nullstiller alt først):

```bash
flask --app app seed
```

Seed-skriptet lager 13 matretter (én upublisert), 4 ordrer med ulike statuser,
2 spørsmål og disse testbrukerne:

| Rolle | E-post | Passord |
|---|---|---|
| Admin | `admin@ektemat.example.test` | `SEED_ADMIN_PASSWORD` i `.env` |
| Kunde | `kari.testkunde@example.test` | `SEED_CUSTOMER_PASSWORD` i `.env` |
| Bedriftskunde | `bedrift.test@example.test` | `SEED_CUSTOMER_PASSWORD` i `.env` |

Standardpassordene står i `.env.example`. Alle navn, adresser og ordrer er oppdiktet.

Tom database uten testdata:

```bash
flask --app app init-db
```

## Kjøre

```bash
flask --app app run --debug
```

Åpne http://127.0.0.1:5000.

| Side | Adresse |
|---|---|
| Forside | `/` |
| Meny (alle arrangementer) | `/meny` |
| Meny for ett arrangement | `/meny/<slug>`, f.eks. `/meny/wedding` |
| Handlekurv | `/handlekurv` |
| Bestilling (krever innlogging) | `/bestilling` |
| Mine ordrer og spørsmål (krever innlogging) | `/mine-ordrer`, `/mine-ordrer/<id>` |
| Registrer deg | `/registrer` |
| Logg inn | `/logg-inn` |
| Administrasjon (kun admin) | `/admin/` |
| Matretter (kun admin) | `/admin/matretter` |
| Ordrer (kun admin) | `/admin/ordrer?status=&fra=&til=` |
| Spørsmål (kun admin) | `/admin/sporsmal`, `/admin/sporsmal?vis=alle` |

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
