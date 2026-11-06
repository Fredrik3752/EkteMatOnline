# Plan 08 – Bilder for matretter (A2)

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Kravet, ordrett fra oppgaveteksten

> **A2 Images.** Upload a picture for each item, **or** write an instruction that an AI agent
> or image service uses to create or modify the picture. The admin previews the result
> before it is saved.

## Tolkning og valg

Kravet har to alternativer, og det holder å oppfylle ett av dem:

1. **Opplasting** av et bilde for hver rett, eller
2. en **instruksjon** som en *AI-agent eller bildetjeneste* bruker til å lage eller endre bildet.

Uansett alternativ skal admin **forhåndsvise resultatet før det lagres**.

Vi bygger **alternativ 1, opplasting med forhåndsvisning før lagring**. Det oppfyller A2
fullt ut, krever ingen betalt API-nøkkel og sender ingen data til tredjeparter.

Vi lager **ikke** en lokal bildegenerator som later som den er en AI- eller bildetjeneste.
Den ville ikke oppfylt alternativ 2 slik det står, og den trengs ikke for å oppfylle A2.

### Ikke med i denne fasen (valgfritt senere)

Alternativ 2 krever en ekte AI-agent eller bildetjeneste. Mulige veier:

- en gratis tjeneste uten nøkkel, for eksempel Pollinations
- en gratis konto med nøkkel, for eksempel Hugging Face Inference
- en betalt tjeneste, for eksempel OpenAI Images

Alle sender instruksjonen til en ekstern tjeneste og har egne vilkår, og flere av dem
krever en nøkkel i `.env`. Valget må produkteieren ta. Opplastingsflyten er laget slik at
et bilde fra en tjeneste kan gå inn i samme forhåndsvisning (`ImageStore.save_preview`),
så alternativ 2 kan legges til senere uten å endre lagring eller visning.

## Flyt

1. `/admin/matretter/<id>/bilde` viser gjeldende bilde, et opplastingsskjema (JPEG, PNG eller
   WebP, høyst 5 MB) og en knapp for å fjerne bildet.
2. `POST …/bilde/forhandsvis` validerer filen og lagrer den **midlertidig** i
   `instance/image_previews/`, som ikke er offentlig. Retten endres ikke.
3. Forhåndsvisningssiden viser nåværende og nytt bilde side om side, og nytt bilde slik det
   blir seende ut på menykortet. Forhåndsvisningen hentes fra
   `GET /admin/bilder/forhandsvisning/<token>`, som bare admin har tilgang til.
4. `POST …/bilde/lagre` flytter bildet til `app/static/uploads/food/` med et tilfeldig filnavn
   og setter `image_path`. Det gamle opplastede bildet slettes.
   `POST …/bilde/forkast` sletter forhåndsvisningen.
5. `POST …/bilde/fjern` fjerner bildet fra retten og sletter filen.

## Sikkerhet

- Filtypen sjekkes ut fra innholdet (magic bytes), ikke filnavnet eller nettleserens content-type.
- Brukerens filnavn brukes aldri. Filene får tilfeldige navn, og det hindrer path traversal.
- Forhåndsvisningen knyttes til retten i sessionen. Man kan ikke lagre en annens token eller
  en token for en annen rett.
- `MAX_CONTENT_LENGTH` (6 MB) stopper store forespørsler før de leses, og gir en vennlig 413-side.
- Bare filer under `uploads/food/` slettes, aldri andre filer i `static/`.
- Opplastede filer committes ikke (`.gitignore`).

## MVC

- `app/models/image.py`: domeneregler (tillatte typer, maks størrelse, `detect_image_type`).
- `app/models/repositories/image_store.py`: all fillagring (midlertidig, permanent, sletting).
  Dette er lagringslaget for bilder og det eneste stedet som skriver filer.
- `app/controllers/admin.py`: rutene. `templates/admin/food_item_image*.html`: visningen.

## Tester

- **Domenet:** JPEG, PNG og WebP godtas. Tekst, GIF, tom fil og for stor fil avvises.
- **Forhåndsvisning:** retten endres ikke, og forhåndsvisningsbildet vises bare for admin.
- **Lagring:** filen flyttes, `image_path` settes, forhåndsvisningen slettes og menykortet viser bildet.
  Et gammelt bilde slettes ved bytte.
- **Forkast og fjern** virker.
- **Feil:**
  - lagre uten forhåndsvisning
  - lagre med forhåndsvisning for en annen rett
  - ugyldig token
  - feil filtype
  - for stor fil og 413
  - manglende fil
- **Tilgang og CSRF:** CSRF gjelder også for multipart, kunden får 403, og ukjent rett gir 404.
