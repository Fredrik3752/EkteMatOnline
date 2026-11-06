# Plan 02 – Domenelag, repositories og seed-data (fase 2)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Mål

Hele modellaget fra MVC: domeneklasser med forretningsregler, repositories for
alle tabeller og et seed-skript med syntetiske data. Ingen nye sider ennå –
fase 3–8 bygger controllere og views oppå dette.

## Domeneklasser (`app/models/`)

| Klasse | Ansvar | Krav |
|---|---|---|
| `User` | kunde eller admin, passord-hash og sjekk (`werkzeug.security`) | C3, sikkerhet |
| `Allergen`, `DietaryLabel`, `EventCategory` | referansedata | A1, C1 |
| `FoodItem` | navn, beskrivelse, pris i øre, minimumsantall, kategorier, allergener, kostholdsmerker, bilde, opprinnelse, publisert. `validate()`, `accepts_quantity()` | A1, C1, C2 |
| `Order` | kunde, eventdato, gjester, adresse, linjer, gjestegrupper, ordre- og betalingsstatus. `change_status()`, `total_ore` | A3, C3, C4 |
| `OrderStatus` | tilstandsmaskin (se under) | A3 |
| `PaymentStatus` | `not_paid`, `deposit_paid`, `invoiced`, `paid` | A3, C4 |
| `OrderLine` | vare, antall og pris på bestillingstidspunktet | C3 |
| `GuestGroup` | antall gjester + allergier/kosthold per gruppe (GDPR) | C3 |
| `Question` | spørsmål om en ordre, `answer()` | A4, C5 |
| `ValidationError`, `InvalidStatusTransition` | domenefeil controllere kan vise til brukeren | – |
| `money.format_nok()` | «1 890,00 kr» | C1, C2 |

### Tilstandsmaskin for ordrestatus

```
submitted ──► approved ──► in_preparation ──► delivered
    │             │               │
    ├──► rejected └──► cancelled ◄┘
    └──► cancelled
```

`delivered`, `rejected` og `cancelled` er slutt-tilstander. Ugyldige overganger
gir `InvalidStatusTransition`. Kunden kan bare avbestille mens ordren er `submitted`.

## Repositories (`app/models/repositories/`)

- `UserRepository` – `add`, `get`, `get_by_email`, `list_customers`
- `EventCategoryRepository`, `AllergenRepository`, `DietaryLabelRepository` – oppslag
- `FoodItemRepository` – `add`, `update`, `delete`, `get`, `list_all`, `list_published_by_category`
- `OrderRepository` – `add` (ordre + linjer + gjestegrupper i én transaksjon), `get`,
  `list(status, date_from, date_to)`, `list_for_customer`, `save_status`
- `QuestionRepository` – `add`, `get`, `list_for_order`, `list_all(unanswered_only)`, `save_answer`

Alle returnerer domeneobjekter. Skriving skjer i transaksjoner (`with db:`).

## Seed-data

`flask --app app seed` nullstiller databasen og legger inn:

- ~12 matretter inspirert av høstmenyen i datapakken (fiskesuppe, Vossalam, rødbetsalat, rakfisk …)
  og flere retter for bursdag, konfirmasjon, bryllup, konferanse og julebord, med allergener,
  opprinnelse og én upublisert kladd
- 1 administrator og 2 testkunder med `example.test`-adresser
- noen ordrer med ulike statuser, gjestegrupper og spørsmål (ett besvart, ett ubesvart)

Alle navn og adresser er oppdiktet. Ingenting hentes fra `customer_emails_export.csv`
eller ordre-eksporten i datapakken. Testpassord leses fra `.env` med standardverdier
dokumentert i `.env.example`.

## Tester

- Tilstandsmaskinen: alle lovlige og noen ulovlige overganger
- Validering av `FoodItem`, `Order`, `GuestGroup`
- Passord-hash og -sjekk
- Repositories: lagre/hente/oppdatere/slette, filtrering, transaksjon ruller tilbake ved feil
- Seed-kommandoen: forventet antall rader, admin finnes, ingen ekte e-postdomener

## Ferdig når

`pytest` er grønn, `flask --app app seed` virker, og arkitekturtesten (ingen
`sqlite3` utenfor repositories) er fortsatt grønn.
