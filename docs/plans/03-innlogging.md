# Plan 03 – Innlogging, registrering og tilgangskontroll (fase 3)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Mål

Kunder kan registrere seg, logge inn og ut (forutsetning for C3–C5). Admin-panelet
er bare tilgjengelig for brukere med rollen `admin` (A1–A4). Skjemaer er beskyttet
mot CSRF.

## Brukerhistorier

- Som **ny kunde** vil jeg registrere meg med navn, e-post og passord, slik at jeg kan bestille.
- Som **kunde** vil jeg logge inn og bli sendt tilbake dit jeg var (f.eks. kassen).
- Som **ansatt i Ekte Mat** vil jeg logge inn og komme rett til admin-panelet.
- Som **Ekte Mat** vil vi at kunder ikke kan åpne admin-sidene.

## Løsning

| Del | Fil | Innhold |
|---|---|---|
| Controller | `app/controllers/account.py` | `GET/POST /registrer`, `GET/POST /logg-inn`, `POST /logg-ut` |
| Controller | `app/controllers/admin.py` | `GET /admin` – oversikt (antall ordrer per status, ubesvarte spørsmål) |
| Hjelpere | `app/controllers/auth.py` | `load_logged_in_user` (setter `g.user`), `@login_required`, `@admin_required`, trygg `next`-redirect |
| Hjelpere | `app/controllers/csrf.py` | token i session, `csrf_token()` i maler, sjekk på alle POST-forespørsler |
| Hjelpere | `app/controllers/errors.py` | 400-, 403- og 404-sider |
| Views | `templates/account/`, `templates/admin/`, `templates/errors/` | skjemaer med feilmeldinger per felt |

Regler:

- Passord hashes i domeneklassen `User` (pbkdf2:sha256). Klartekst lagres aldri.
- Innlogging: `session.clear()` før `user_id` settes. Samme feilmelding for ukjent e-post og feil passord.
- `next` godtas bare som relativ sti (`/…`, ikke `//…`), ellers åpen omdirigering.
- Utlogging skjer med POST (med CSRF-token), ikke en lenke.
- Uinnlogget → omdirigeres til innlogging. Innlogget kunde på admin-side → 403.
- Cookie: `HttpOnly` og `SameSite=Lax`.
- Ingen ny avhengighet (ikke Flask-Login/Flask-WTF) – det som trengs er noen få linjer.

## Tester

Registrering (ok, duplikat, ugyldige felt, ulike passord), innlogging (ok, feil passord,
ukjent e-post, `next`, åpen omdirigering avvises), utlogging, tilgang til `/admin` for
anonym/kunde/admin, POST uten CSRF-token gir 400.

## Ferdig når

`pytest` er grønn, og man kan registrere seg, logge inn som kunde og admin, og
logge ut i nettleseren.
