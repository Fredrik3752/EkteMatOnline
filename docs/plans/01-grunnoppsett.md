# Plan 01 – Grunnoppsett (fase 1)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Mål

En kjørbar Flask-applikasjon med tydelig MVC-struktur, SQLite-skjema for hele
domenet, ett repository som viser mønsteret, en enkel forside og tester. Ingen
funksjoner fra A1–A4 / C1–C5 ennå.

## Beslutninger

| Tema | Valg | Begrunnelse |
|---|---|---|
| Backend | Flask 3.1 med app factory (`create_app`) | Oppgavekrav; factory gjør testing enkelt |
| View | Jinja2-maler + vanlig CSS/JS | Enklest; oppfyller kravet til front end |
| Lagring | SQLite via `sqlite3` i standardbiblioteket | Oppgaven tillater SQLite midlertidig |
| Datatilgang | Kun repository-klasser i `app/models/repositories/` | Neo4j skal kunne erstatte SQLite i oblig 5 uten endringer i controllere/views |
| Domene | `dataclass`-klasser i `app/models/` | Controllere og views ser domeneobjekter, ikke databaserader |
| Priser | Heltall i øre (`price_ore`) | Unngår avrundingsfeil med flyttall |
| Språk | Kode og kommentarer på engelsk, brukergrensesnitt på norsk | Bedriften er i Bergen; NO/EN er et valgfritt tillegg |
| Konfig | `.env` (ignoreres) + `.env.example` | Ingen hemmeligheter i Git |
| Tester | pytest med midlertidig database per test | Isolerte, raske tester |
| Bilder (A2, fase 8) | Opplasting + lokal «generator» uten betalt API (Pillow) | Oppgaven krever ingen bestemt tjeneste |

## Mappestruktur

```
app/
  __init__.py                 create_app, blueprints, CLI
  config.py                   konfigurasjon fra miljøvariabler
  models/                     M – domeneklasser
    event_category.py
    repositories/             M – eneste kode som rører SQLite
      database.py             tilkobling, init_db, CLI-kommando
      schema.sql              tabeller + referansedata
      event_category_repository.py
  controllers/                C – Flask-blueprints
    shop.py                   forside (senere meny, kurv, bestilling)
  templates/                  V – Jinja2
    base.html
    shop/index.html
  static/css/style.css
tests/
docs/plans/
```

## Databaseskjema (hele domenet, brukes fra fase 2)

- `users` – kunder og administratorer (`role`: customer/admin), hashet passord
- `event_categories` – bursdag, konfirmasjon, bryllup, konferanse, julebord, …
- `allergens` – de 14 EU-allergenene
- `dietary_labels` – vegetar, vegansk, glutenfri, laktosefri, …
- `food_items` – navn, beskrivelse, pris, minimumsantall, bilde, opprinnelse, publisert
- `food_item_categories`, `food_item_allergens`, `food_item_dietary_labels` – koblingstabeller
- `orders` – kunde, eventdato, gjester, adresse, ordrestatus, betalingsstatus
- `order_lines` – vare, antall og pris *på bestillingstidspunktet*
- `guest_groups` – allergier og kosthold per gjestegruppe (ikke per navngitt person, jf. GDPR-notatet)
- `questions` – spørsmål om en ordre og svaret fra Ekte Mat

Ordrestatus: `submitted → approved → in_preparation → delivered`, eller
`rejected` / `cancelled`. Betalingsstatus: `not_paid`, `deposit_paid`,
`invoiced`, `paid`. Lovlige verdier sikres med `CHECK` i skjemaet; selve
overgangsreglene kommer i domenelaget i fase 2.

## Leveranser i fase 1

1. `.gitignore` utvidet (oppgave-PDF, `.DS_Store`, `instance/`, pytest-cache)
2. `requirements.txt`, `.env.example`
3. App factory, konfig, databasemodul med `flask init-db`
4. Skjema med referansedata (eventkategorier, allergener, kostholdsmerker)
5. `EventCategory` + `EventCategoryRepository` som første eksempel på mønsteret
6. Forside (`shop.index`) som viser eventkategoriene – går gjennom alle tre lag
7. `CLAUDE.md` og `README.md`
8. Tester: app factory, forside, skjema, repository, init-db-kommandoen

## Ferdig når

- `pytest` er grønn
- `flask --app app run` starter og forsiden svarer 200
- Ingen fil utenfor `app/models/repositories/` importerer `sqlite3`
- Ingen persondata, API-nøkler eller oppgave-PDF i Git

## Utenfor fase 1

Seed-skript og domenelogikk (fase 2), innlogging (fase 3), funksjonene A1–A4 og C1–C5 (fase 4–8).
