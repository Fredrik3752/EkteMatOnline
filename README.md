# Ekte Mat Online

INFO212 – Obligatorisk innlevering 4 og 5. Bestillingsløsning for den fiktive
cateringbedriften Ekte Mat AS i Bergen: kundeside og administrasjonspanel, bygget med
Flask og Jinja2 etter MVC-mønsteret.

> Alle personer, bedrifter og data i prosjektet er syntetiske.

**Lagring:** **Neo4j** (Oblig 5) eller **SQLite**. Lagringen velges med `STORAGE_BACKEND` i `.env`,
og alle funksjoner virker likt med begge. Controllere og views er identiske med `oblig4`-versjonen;
bare repository-laget i modellen er byttet ut. Se [Neo4j](#neo4j-oblig-5) og
[grafdatamodellen](docs/design/grafmodell.md).

| Versjon | Git | Lagring |
|---|---|---|
| Oblig 4 | taggen `oblig4` (og `main`) | SQLite |
| Oblig 5 | grenen `oblig5-neo4j` | Neo4j eller SQLite |

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
- For Neo4j: Docker Desktop (eller annen Docker med `docker compose`). Ingen Neo4j-konto trengs.

## Installere

```bash
git clone https://github.com/Fredrik3752/EkteMatOnline.git
cd EkteMatOnline
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
```

Sett egne verdier i `.env`: `SECRET_KEY`, og for Neo4j `NEO4J_PASSWORD` og `NEO4J_TEST_PASSWORD`
(minst 8 tegn). `.env` er ignorert av Git og skal aldri committes.

## Seede databasen (SQLite, standard)

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

Testene (381 stk.) kjører mot SQLite med en midlertidig database og bildemappe per test, og rører
ikke `instance/` eller `app/static/uploads/`. Neo4j trengs ikke. Testene som gjelder Neo4j
spesielt, hoppes over med en melding hvis test-containeren ikke kjører.

- `tests/test_repositories.py` er kontrakttester: hver test kjøres mot **både** SQLite og Neo4j.
- `tests/test_architecture.py` sjekker MVC-regelen. Bare `repositories/sqlite/` bruker SQLite, bare
  `repositories/neo4j/` bruker Neo4j, og controllerne importerer aldri en bestemt lagring.

## Neo4j (Oblig 5)

Neo4j 5.26 (Community) kjører lokalt i Docker. [`docker-compose.yml`](docker-compose.yml) starter to
databaser, begge bare tilgjengelige fra egen maskin:

| Container | Porter | Brukes til |
|---|---|---|
| `ektemat-neo4j-dev` | 7474 (Browser), 7687 (Bolt) | appen. Dataene overlever omstart (volum) |
| `ektemat-neo4j-test` | 7475 (Browser), 7688 (Bolt) | testene. **Tømmes før hver test** |

### Starte appen med Neo4j

```bash
docker compose up -d                          # start begge databasene
docker compose ps                             # vent til begge er "healthy"
STORAGE_BACKEND=neo4j flask --app app seed    # nullstill og fyll inn syntetiske testdata
STORAGE_BACKEND=neo4j flask --app app run --debug
```

Du kan også sette `STORAGE_BACKEND=neo4j` i `.env`, så slipper du prefikset. Testbrukerne er de samme
som for SQLite (se tabellen over). Med en tom database setter appen opp skjema, unikhetsregler og
referansedata selv ved første oppstart.

### Teste mot Neo4j

```bash
TEST_STORAGE_BACKEND=neo4j pytest             # hele samlingen (381) mot neo4j-test
```

Testene velger lagring med `TEST_STORAGE_BACKEND` og bruker bare `NEO4J_TEST_URI`. De bruker aldri
`STORAGE_BACKEND` eller utviklingsdatabasen fra `.env`.

### Se grafen i Neo4j Browser

Åpne http://localhost:7474. Logg inn med `localhost:7687`, bruker `neo4j` og `NEO4J_PASSWORD` fra
`.env`. Prøv `CALL db.schema.visualization()`. Flere spørringer står i
[docs/design/grafmodell.md](docs/design/grafmodell.md).

### Sikkerhet og feilsøking

- **Sikker nullstilling:** `seed` og `init-db` tømmer bare en Neo4j-database som er tom eller laget av appen
  (markørnoden `:EkteMatStorage`). En database med andre data blir aldri slettet.
- **Ingen kontakt:** feilmeldingen «Får ikke kontakt med Neo4j» betyr at containeren ikke kjører. Kjør `docker compose up -d`.
- **Feil passord:** passordet settes første gang en container starter. Har du endret `NEO4J_PASSWORD` etterpå,
  må du starte på nytt med `docker compose down -v`. Det **sletter** utviklingsdataene.
- **Tilbake til SQLite:** fjern `STORAGE_BACKEND=neo4j`, eller sett `STORAGE_BACKEND=sqlite`.
- **Stoppe:** `docker compose stop` stopper databasene og beholder dataene.

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
    repositories/        M – all datatilgang: kontrakter (base.py), offentlige navn, image_store.py
      sqlite/            M – SQLite-implementasjonen (schema.sql)
      neo4j/             M – Neo4j-implementasjonen (Cypher, driver, skjema)
  controllers/           C – Flask-blueprints: shop, cart, checkout, account, admin
  templates/             V – Jinja2-maler
  static/                CSS og opplastede bilder
tests/                   pytest
docs/plans/              planen for hver fase, skrevet før koden
docs/design/             brukerhistorier og diagrammer (Mermaid)
docs/screenshots/        skjermbilder til rapporten
docker-compose.yml       Neo4j for utvikling og test
CLAUDE.md                prosjektbeskrivelse og regler for Claude Code
```
