# Plan 05 – Handlekurv (C2) og bestilling (C3)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Brukerhistorier

- **C2** Som kunde vil jeg legge retter i en handlekurv, endre antall og fjerne dem, og se
  estimert totalpris, slik at jeg kan sette sammen bestillingen før jeg sender den.
  Antall under minimum for en rett skal ikke godtas.
- **C3** Som kunde vil jeg logge inn (eller registrere meg) og sende bestillingen med
  eventdato, antall gjester, leveringsadresse og allergier og kosthold per gjestegruppe,
  slik at kjøkkenet får alt i én bestilling. Det trengs ingen betaling.
- Som kjøkken vil vi ha allergier per *gjestegruppe*, ikke per navngitt gjest (GDPR-notatet,
  art. 9), og vi vil aldri få en bestilling med færre enn minimumsantallet.

## Model

`app/models/cart.py`:

- `Cart` og `CartLine` er rene domeneklasser uten Flask eller database.
- `Cart.build(quantities, items)` lager handlekurven fra `{item_id: antall}` og
  `FoodItem`-objekter. Retter som er slettet eller avpublisert fjernes, og navnene meldes tilbake.
- `check_quantity(item, qty)` gir `ValidationError` når antallet er under minimum, over maks
  (10 000) eller ikke et heltall.
- `Cart.problems()` lister linjer som ikke lenger oppfyller minimum, for eksempel når admin har
  økt minimumsantallet etter at retten ble lagt i kurven.
- `Cart.to_order_lines()` kopierer navn og pris på bestillingstidspunktet.

Handlekurven lagres i Flask-session som `{"<item_id>": antall}`. Den er brukerens
nettleserdata, ikke forretningsdata, så den går ikke via repository. Ordren lagres
via `OrderRepository` som før.

## Controllere

`app/controllers/cart.py` (blueprint `cart`):

| Rute | Metode | Innhold |
|---|---|---|
| `/handlekurv` | GET | linjer, antall, linjesum, estimert total, advarsler |
| `/handlekurv/legg-til` | POST | `item_id`, `quantity`. Legges til det som finnes, og totalen må være ≥ minimum |
| `/handlekurv/oppdater` | POST | sett nytt antall (≥ minimum) |
| `/handlekurv/fjern` | POST | fjern linjen |

`app/controllers/checkout.py` (blueprint `checkout`, `@login_required`):

| Rute | Metode | Innhold |
|---|---|---|
| `/bestilling` | GET/POST | skjema og oppsummering. Ved suksess lagres ordren og kurven tømmes |
| `/bestilling/<id>/kvittering` | GET | bekreftelse, bare for kunden som eier ordren (ellers 404) |

- **Gjestegrupper:** tre rader vises fra start, og en knapp med litt JavaScript legger til flere.
  Skjemaet virker også uten JavaScript. Tomme rader ignoreres, og minst én gruppe kreves.
- **Validering:** domenet sjekker dato etter i dag, antall gjester ≥ 1, adresse, og at
  gjestegruppene til sammen ikke har flere gjester enn bestillingen. Controlleren sjekker i
  tillegg tom kurv og linjer under minimum.
- **Innlogging:** `log_in()` tømmer sessionen for å hindre session fixation, men skal
  **beholde handlekurven**. Ellers mister kunden kurven når hen logger inn i kassen.

## Views

- Menykortet får et skjema med antall (forhåndsutfylt med minimum, `min`-attributt) og
  «Legg i handlekurv».
- `cart/cart.html`, `checkout/checkout.html` og `checkout/receipt.html`.
- Toppmenyen viser «Handlekurv (n)».

## Tester

- **Domenet:** bygge kurven, fjerne retter som er borte, total, `check_quantity`, `problems()`.
- **Kurv:** legge til (også under minimum og ukjent rett), legge sammen antall, oppdatere,
  fjerne, CSRF, og tellingen i menyen.
- **Bestilling:**
  - krever innlogging, og kurven overlever innloggingen
  - tom kurv sendes tilbake til kurven
  - suksess lagrer ordre, linjer og gjestegrupper og tømmer kurven
  - valideringsfeil: dato, adresse, gjester, grupper
  - linje under minimum blokkerer bestillingen
  - kvitteringen vises bare for eieren
