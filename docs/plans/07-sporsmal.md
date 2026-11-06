# Plan 07 – Spørsmål om ordrer (C5) og svar fra Ekte Mat (A4)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Brukerhistorier

- **C5** Som kunde vil jeg stille et spørsmål om en bestemt ordre og lese svaret fra Ekte Mat
  på samme sted, slik at jeg slipper e-post og telefon.
- **A4** Som eventkoordinator vil jeg se alle spørsmål, med de ubesvarte først, og svare
  direkte, slik at ingen henvendelser blir liggende. Problemet fra datapakken var at
  forespørsler ble borte i e-posten.

## Model

`Question` har fra før `validate()`, `give_answer()` og `is_answered`. Nye regler:

- Spørsmålet kan være høyst 2000 tegn og svaret høyst 4000 tegn.
- Et besvart spørsmål kan ikke besvares på nytt. Det hindrer at to ansatte overskriver
  hverandres svar. Forsøk gir `ValidationError`.

Repositoryet har det som trengs (`add`, `get`, `list_for_order`, `list_all(unanswered_only)`,
`save_answer`). Det eneste nye er `QuestionRepository.count_unanswered()` til menyen og oversikten.

## Kunde (C5) – `app/controllers/account.py`

| Rute | Metode | Innhold |
|---|---|---|
| `/mine-ordrer/<id>` | GET | ordreside med seksjonen «Spørsmål om ordren»: spørsmål, tidspunkt og svar, eller «Venter på svar» |
| `/mine-ordrer/<id>/sporsmal` | POST | nytt spørsmål. Bare på egen ordre, ellers 404 |

Kunden kan stille spørsmål uansett ordrestatus. Et spørsmål om en levert ordre er også nyttig.

## Admin (A4) – `app/controllers/admin.py`

| Rute | Metode | Innhold |
|---|---|---|
| `/admin/sporsmal` | GET | liste med fanene «Ubesvarte» (standard) og «Alle»: ordre, kunde, spørsmål, tidspunkt og svarskjema |
| `/admin/sporsmal/<id>/svar` | POST | lagre svar. Tilbake til `next` (listen eller ordresiden) |

- Ordresiden i admin viser spørsmålene til ordren med svarskjema.
- Admin-menyen viser «Spørsmål (n)» med antall ubesvarte, og kortet på oversikten lenker hit.

## Tester

- **Kunde:** stille spørsmål (gyldig, tomt, for langt), andres ordre gir 404, krever innlogging
  og CSRF. Spørsmål og svar vises på ordresiden.
- **Admin:**
  - tilgang: kunde får 403, anonym blir omdirigert
  - listen viser ubesvarte som standard, og «Alle» viser alt
  - svar fra listen og fra ordresiden, med `next` som omdirigering
  - tomt svar og nytt svar på et besvart spørsmål avvises
  - antallet i menyen stemmer
- **Domenet:** regler for lengde og dobbelt svar.
