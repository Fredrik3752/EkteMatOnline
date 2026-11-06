# Ekte Mat Online

INFO212 – Obligatorisk innlevering 4. En første versjon av bestillingsløsningen
for den fiktive cateringbedriften Ekte Mat AS i Bergen: kundeside og
administrasjonspanel, bygget med Flask, Jinja2 og SQLite etter MVC-mønsteret.

> Alle personer, bedrifter og data i prosjektet er syntetiske.
> Neo4j er **ikke** med i denne versjonen. Lagringen er SQLite bak repository-klasser.

## Funksjoner

| Krav | Funksjon | Side |
|---|---|---|
| C1 | Meny med kort gruppert etter arrangement: bilde, pris, minimumsantall, allergener og opprinnelse | `/meny`, `/meny/<slug>` |
| C2 | Handlekurv: legg til, endre og fjern, med estimert total. Antall under minimum avvises | `/handlekurv` |
| C3 | Bestilling med innlogging eller registrering: eventdato, gjester, adresse og gjestegrupper med allergier og kosthold | `/bestilling` |
| C4 | Mine ordrer med ordrestatus og betalingsstatus, og avbestilling før godkjenning | `/mine-ordrer` |
| C5 | Spørsmål om en ordre, og svaret fra Ekte Mat | `/mine-ordrer/<id>` |
| A1 | Matretter: opprett, rediger, publiser og slett, med arrangementer, allergener og kosthold | `/admin/matretter` |
| A2 | Bilde per rett: last opp, forhåndsvis og lagre eller forkast (se under) | `/admin/matretter/<id>/bilde` |
| A3 | Ordrer: filter på status og eventdato, og ordreside med ordrestatus (tilstandsmaskin) og betalingsstatus | `/admin/ordrer` |
| A4 | Spørsmål: ubesvarte først, og svar fra listen eller ordresiden | `/admin/sporsmal` |

Tillegg som dekker behov i datapakken:
- opprinnelsen til råvarene på hvert menykort (eieren)
- allergier per gjestegruppe og ikke per navngitt gjest (GDPR-notatet)
- handlekurven beholdes ved innlogging

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
cp .env.example .env             # Windows: copy .env.example .env – sett en egen SECRET_KEY
```

## Seede databasen

Databasen (`instance/ektemat.db`) opprettes automatisk ved første oppstart.
Fyll den med syntetiske testdata. Kommandoen nullstiller alt først:

```bash
flask --app app seed
```

Seed-skriptet lager 13 matretter (én upublisert), 4 ordrer med ulike statuser,
2 spørsmål (ett besvart) og disse testbrukerne:

| Rolle | E-post | Passord |
|---|---|---|
| Admin | `admin@ektemat.example.test` | `SEED_ADMIN_PASSWORD` i `.env` |
| Kunde | `kari.testkunde@example.test` | `SEED_CUSTOMER_PASSWORD` i `.env` |
| Bedriftskunde | `bedrift.test@example.test` | `SEED_CUSTOMER_PASSWORD` i `.env` |

Standardpassordene står i `.env.example`. Alle navn, adresser og ordrer er oppdiktet.
`flask --app app init-db` gir en tom database uten testdata.

## Kjøre

```bash
flask --app app run --debug
```

Åpne http://127.0.0.1:5000. Admin-panelet ligger på `/admin/`.

## Teste

```bash
pytest
```

Testene (320 stk.) bruker en midlertidig database og bildemappe per test, og rører ikke
`instance/` eller `app/static/uploads/`. `tests/test_architecture.py` sjekker MVC-regelen om
at bare repository-klassene bruker SQLite.

## Bilder (krav A2)

Oppgaven sier: *«Upload a picture for each item, **or** write an instruction that an AI agent
or image service uses to create or modify the picture. The admin previews the result before
it is saved.»*

Løsningen bruker det første alternativet, **opplasting**:
- Admin velger et bilde (JPEG, PNG eller WebP, høyst 5 MB) og ser det på en egen
  forhåndsvisningsside, side om side med nåværende bilde og slik menykortet blir.
- Bildet lagres først når admin trykker «Lagre bildet». «Forkast» sletter forhåndsvisningen.
- Opplastede bilder lagres i `app/static/uploads/food/` og committes ikke. `flask seed`
  fjerner dem, fordi rettene de hørte til blir slettet.

Det andre alternativet, instruksjon til en AI-agent eller bildetjeneste, er ikke laget,
fordi det krever en ekstern tjeneste. Se `docs/plans/08-bilder.md`.

## Struktur (MVC)

```
app/
  models/                M – domeneklasser og forretningsregler (Order, FoodItem, Cart, …)
    repositories/        M – all datatilgang: SQLite og bildefiler (byttes mot Neo4j i oblig 5)
  controllers/           C – Flask-blueprints: shop, cart, checkout, account, admin
  templates/             V – Jinja2-maler
  static/                CSS og opplastede bilder
tests/                   pytest
docs/plans/              planen for hver fase, skrevet før koden
docs/design/             brukerhistorier og diagrammer (Mermaid)
docs/screenshots/        skjermbilder til rapporten
CLAUDE.md                prosjektbeskrivelse og regler for Claude Code
```
