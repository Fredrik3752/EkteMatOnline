# Plan 04 – Matretter i admin (A1) og meny per arrangement (C1)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Brukerhistorier

- **A1** Som kjøkkensjef vil jeg legge til, endre og fjerne retter med navn, beskrivelse,
  pris, minimumsantall, arrangementstyper, allergener, kostholdsmerker og opprinnelse,
  og bestemme om retten er publisert, slik at menyen alltid er oppdatert.
- **C1** Som kunde vil jeg se rettene som kort gruppert etter type arrangement, med bilde,
  pris, minimumsantall og allergener, slik at jeg raskt finner mat til mitt arrangement.
- **Tillegg** Som eier vil jeg at hvert kort viser hvor råvarene kommer fra.
  Feltet `origin` finnes allerede, så dette koster lite.

## Admin (A1) – `app/controllers/admin.py`

| Rute | Metode | Innhold |
|---|---|---|
| `/admin/matretter` | GET | tabell: navn, pris, min., arrangementer, publisert |
| `/admin/matretter/ny` | GET/POST | skjema for ny rett |
| `/admin/matretter/<id>/rediger` | GET/POST | samme skjema, utfylt |
| `/admin/matretter/<id>/publiser` | POST | slå publisering av/på |
| `/admin/matretter/<id>/slett` | POST | slett etter bekreftelse |

- Skjemaet bruker avkrysningsbokser for arrangementer, allergener og kostholdsmerker.
- Pris skrives i kroner («189» eller «189,50») og gjøres om til øre med `nok_to_ore`.
- Feil vises ved hvert felt, og skjemaet beholder det brukeren skrev (HTTP 400).
- Bildefeltet (`image_path`) beholdes uendret ved redigering. Bilder kommer i fase 8 (A2).
- Når en rett slettes, beholder eksisterende ordrer navn og pris. `order_lines.food_item_id`
  settes til `NULL` (allerede i skjemaet). Bekreftelsesteksten sier dette.
- Admin-sidene får en felles undermeny: Oversikt · Matretter.

## Kundeside (C1) – `app/controllers/shop.py`

| Rute | Innhold |
|---|---|
| `/meny` | alle publiserte retter, én seksjon per arrangement, hurtiglenker øverst |
| `/meny/<slug>` | bare ett arrangement; 404 for ukjent slug |

- Kortene på forsiden lenker til `/meny/<slug>`.
- Hvert kort (`templates/shop/_food_card.html`) viser bilde (eller en plassholder), navn,
  beskrivelse, pris, minimumsantall, allergener, kostholdsmerker og opprinnelse.
- Upubliserte retter vises aldri på kundesiden.
- Knappen «Legg i handlekurv» kommer i fase 5 (C2).

## Model

- `FoodItemRepository.list_published_in_category(category_id)`
- Skjemaets ID-er gjøres om til domeneobjekter ved å filtrere `list_all()` fra
  referanse-repositoriene. Listene er små, så det trengs ingen egne oppslag.

## Tester

- Tilgang: anonym blir omdirigert, kunde får 403, admin får 200 på alle admin-rutene.
- Opprett gyldig rett med koblinger. Ugyldig pris, navn og minimum gir 400, og ingenting lagres.
- Rediger (bildet beholdes), publiser/avpubliser, slett, og 404 for ukjent ID.
- En slettet rett i en eksisterende ordre beholder navn og pris på ordrelinjen.
- Meny: viser publiserte og skjuler upubliserte retter, grupperer etter arrangement, kortet viser
  pris, minimum, allergener og opprinnelse, filtrering på slug virker, og ukjent slug gir 404.
