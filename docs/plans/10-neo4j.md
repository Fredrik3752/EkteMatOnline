# Plan 10 – Neo4j som lagringslag (Oblig 5)

Status: godkjent av produkteier (Fredrik), 2026-11-06. Gren: `oblig5-neo4j`. `main` og taggen `oblig4` røres ikke.

## Kravet

Fra oppgaveteksten for Oblig 4:

> Neo4j is the storage layer of the finished system. For this assignment a temporary store such as
> SQLite or JSON files is fine, as long as only repository classes in the model layer touch it, so that
> Neo4j can later replace it **without changes to controllers or views**.

Forelesning 8 og 10 bruker property graph, Cypher og den offisielle Python-driveren (`neo4j`), med
databasekoden i modellaget. Rapporten skal si på forsiden om Neo4j er med, og den kan vise en grafdatamodell.

## Mål

1. Neo4j kan brukes som lagring for **alle** eksisterende funksjoner (A1–A4, C1–C5).
2. SQLite virker fortsatt og er standardvalget. Lagringen velges med `STORAGE_BACKEND=sqlite|neo4j`.
3. **Ingen endringer** i `app/controllers/` eller `app/templates/`. Akseptkriterium:
   `git diff oblig4 -- app/controllers app/templates` er tom.

## Arkitektur

```
app/models/repositories/
  base.py                    kontrakter (ABC) for hvert repository
  backend.py                 velger implementasjon ut fra STORAGE_BACKEND
  storage.py                 init_app, reset_storage, CLI init-db (uavhengig av lagring)
  *_repository.py            offentlige navn som før – FoodItemRepository() gir riktig implementasjon
  image_store.py             uendret – bildene er filer uansett lagring
  sqlite/                    dagens kode, flyttet uendret (database.py, schema.sql, repositories)
  neo4j/                     driver.py, schema.py, repositories i Cypher
```

## Grafmodell

| Node | Viktige egenskaper | Unik |
|---|---|---|
| `User` | id, email, name, phone, role, password_hash, created_at | id, email |
| `EventCategory` | id, slug, name, sort_order | id, slug |
| `Allergen`, `DietaryLabel` | id, code, name | id, code |
| `FoodItem` | id, name, description, price_ore, min_order_qty, image_path, origin, is_published, created_at, updated_at | id |
| `Order` | id, event_date, guest_count, delivery_address, notes, status, payment_status, estimated_total_ore, created_at, updated_at | id |
| `OrderLine` | id, item_name, quantity, unit_price_ore | id |
| `GuestGroup` | id, description, guest_count, allergy_notes, dietary_notes | id |
| `Question` | id, body, created_at, answer, answered_at | id |
| `Counter` | name, value (heltalls-ID-er) | name |

Relasjoner:
- `(:FoodItem)-[:SUITABLE_FOR]->(:EventCategory)`
- `(:FoodItem)-[:CONTAINS]->(:Allergen)`
- `(:FoodItem)-[:HAS_LABEL]->(:DietaryLabel)`
- `(:User)-[:PLACED]->(:Order)`
- `(:Order)-[:HAS_LINE]->(:OrderLine)-[:OF_ITEM]->(:FoodItem)`
- `(:Order)-[:HAS_GUEST_GROUP]->(:GuestGroup)`
- `(:User)-[:ASKED]->(:Question)-[:ABOUT]->(:Order)`
- `(:User)-[:ANSWERED]->(:Question)`

Valg:
- **Heltalls-ID-er** fra `Counter`-noder, slik at URL-ene og domenet ikke endres. Neo4js interne
  `elementId` er ikke stabil.
- **Samme semantikk som i SQLite:**
  - Sletting av `FoodItem` fjerner `OF_ITEM`. Ordrelinjen beholder navn og pris, og `food_item_id` blir `None`.
  - Ordre, linjer og gjestegrupper lagres i én skrivetransaksjon.
- **Regler som tilsvarer `CHECK`** finnes ikke i Neo4j Community. De håndheves i domeneklassene
  (`Order.change_status`, `validate()`), som allerede er testet. Unikhet håndheves med constraints.
- **Tidspunkter** lagres som UTC-tekst (`YYYY-MM-DD HH:MM:SS`), likt SQLite, slik at `|local_time` virker uendret.

## Drift: Docker lokalt

- `docker-compose.yml` med to containere (`neo4j:5.26-community`, LTS), begge bundet til `127.0.0.1`:
  - `neo4j-dev` (7474/7687) med volum, for utvikling og demo
  - `neo4j-test` (7475/7688) uten volum, bare for tester
- Passord ligger i `.env` (ignorert). `.env.example` har plassholdere.
- Testene tømmer databasen før hver test. `reset` nekter å tømme en database som ikke har markørnoden
  `(:EkteMatStorage {purpose})` med riktig formål, eller som ikke er satt opp som test-database.

## Faser

| Fase | Innhold | Ferdig når |
|---|---|---|
| N1 | `base.py`, `backend.py`, `storage.py`, SQLite flyttet til `sqlite/`, offentlige navn beholdt | 320 tester grønne, og controllere og views er uendret |
| N2 | `docker-compose.yml`, `neo4j>=5.28,<6` (versjon 6 krever Python 3.10), config, driver, constraints, referansedata, sikker reset, `init-db` for Neo4j | Appen starter mot Neo4j. Infrastruktur-tester grønne |
| N3 | Repositoryene i Cypher, med kontrakttester som kjører mot begge | Kontrakttestene er grønne for begge |
| N4 | Seed for Neo4j. Hele testsamlingen mot Neo4j (`TEST_STORAGE_BACKEND=neo4j`). Nettlesertest av alle funksjonene | Alt grønt med Neo4j |
| N5 | Grafmodell i `docs/design/`, README om å bytte lagring og om Docker, CLAUDE.md, push av grenen | Dokumentert og pushet |

## Testing

- Vanlig `pytest` kjører bare mot SQLite, så den som vurderer oppgaven trenger ikke Neo4j.
- `TEST_STORAGE_BACKEND=neo4j pytest` kjører hele samlingen mot test-containeren.
  Testene hoppes over med en melding hvis Neo4j ikke svarer.
- SQLite-spesifikke tester (skjema, `CHECK`, rå SQL) kjører bare mot SQLite. Tilsvarende tester for
  Neo4j sjekker constraints og grafstrukturen.
- Arkitekturtesten utvides: `sqlite3` bare i `repositories/sqlite/`, og `neo4j` bare i `repositories/neo4j/`.
