# Plan 06 – Ordrebehandling i admin (A3) og «Mine ordrer» (C4)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Brukerhistorier

- **A3** Som eventkoordinator vil jeg se alle ordrer, filtrere dem på status og eventdato,
  og åpne én ordre for å endre ordrestatus og betalingsstatus, slik at jeg slipper Excel-arket.
- **C4** Som kunde vil jeg se mine egne ordrer med gjeldende status og betalingsstatus.
- **C4 (tillegg)** Som kunde vil jeg kunne avbestille en ordre som ennå ikke er godkjent.
  Regelen finnes allerede i domenet (`can_be_cancelled_by_customer`).

## Admin (A3) – `app/controllers/admin.py`

| Rute | Metode | Innhold |
|---|---|---|
| `/admin/ordrer` | GET | tabell med nr., eventdato, kunde, gjester, total, status og betaling. Filter: `status`, `fra`, `til` (datoer) |
| `/admin/ordrer/<id>` | GET | kunde, levering, retter, gjestegrupper (allergier uthevet), kommentar, statusskjemaer |
| `/admin/ordrer/<id>/status` | POST | ny ordrestatus via `Order.change_status()` (tilstandsmaskinen) |
| `/admin/ordrer/<id>/betaling` | POST | ny betalingsstatus |

- Ordresiden viser bare de overgangene som er lovlige fra gjeldende status, som knapper
  («Godkjenn», «Avvis», «Start tilberedning», «Marker som levert», «Kanseller»).
  Avvisning og kansellering krever bekreftelse.
- En ulovlig overgang sendt direkte, for eksempel `submitted → delivered`, gir en
  feilmelding, og ordren endres ikke.
- Ugyldige filterverdier, som ukjent status eller feil dato, ignoreres med en melding,
  og listen vises uten det filteret.
- Tallene på admin-oversikten lenker til listen, filtrert på hver status.
- `UserRepository.get_many(ids)` henter kundenavn til listen uten én spørring per rad.

## Kunde (C4) – `app/controllers/account.py`

| Rute | Metode | Innhold |
|---|---|---|
| `/mine-ordrer` | GET | egne ordrer, nyeste arrangement først, med status og betalingsstatus |
| `/mine-ordrer/<id>` | GET | detaljer for egen ordre. Andres ordrer gir 404 |
| `/mine-ordrer/<id>/avbestill` | POST | bare mens status er `submitted` |

- Toppmenyen får lenken «Mine ordrer» når brukeren er innlogget.
- Ordredetaljene (fakta, retter og gjestegrupper) legges i ett felles partial,
  `templates/orders/_details.html`, som brukes av kvitteringen, kundesiden og admin-siden.

## Tester

- **Tilgang:** anonym blir omdirigert, kunde får 403 på admin-sidene, og en kunde får 404
  på en annen kundes ordre.
- **Filtre:** status, fra-dato, til-dato, kombinasjoner og ugyldige verdier.
- **Statusoverganger:** hele kjeden fra `submitted` til `delivered`, ulovlige overganger
  avvises, og betalingsstatus endres, også med ugyldig verdi.
- **Kunde:** listen viser bare egne ordrer, detaljsiden virker, avbestilling er lov når
  status er `submitted`, ellers ikke, og alle POST-forespørsler krever CSRF.
