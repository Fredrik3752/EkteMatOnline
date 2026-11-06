# Plan 09 – Ferdigstilling for innlevering

Status: godkjent av produkteier (Fredrik), 2026-11-06

## Mål

Repoet skal kunne vurderes slik det står. README-oppskriften skal virke på en ren maskin,
og rapporten (del 2 og 3) skal ha skjermbilder og diagrammer å bygge på.

## Oppgaver

1. **README og CLAUDE.md:** en tabell fra krav (A1–A4, C1–C5) til side, kjøre- og testkommandoer
   som er verifisert, testbrukere, A2-valget, «Neo4j: nei», og at riktig `DATABASE`-sti står i `.env.example`.
2. **Designdiagrammer** i `docs/design/` som Mermaid, som GitHub viser direkte:
   - brukerhistorier per krav
   - use case-diagram
   - domeneklassediagram
   - tilstandsmaskin for ordrestatus
   - sekvensdiagram for bestilling (C3)
   - MVC-arkitekturskisse

   Alle diagrammene er laget ut fra koden slik den er, ikke fra et ønsket design.
3. **Skjermbilder** i `docs/screenshots/` av alle sidene rapporten krever:
   - kundeside: meny, handlekurv, bestillingsskjema, mine ordrer og spørsmål
   - admin: matretter, bilde, ordreliste og ordreside

   Bare syntetiske data.
4. **Ren klone:** klone repoet til en tom mappe, følge README ordrett (venv, install, seed,
   test, run) og rette det som ikke stemmer.
5. **Sikkerhetsskann av hele git-historikken:** ingen nøkler, ingen persondata, ingen PDF,
   ingen database og ingen filer fra datapakken.
6. Committe lokalt. Push og taggen `oblig4` gjøres først når produkteieren ber om det.
