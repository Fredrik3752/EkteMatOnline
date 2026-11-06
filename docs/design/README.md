# Design – Ekte Mat Online

Diagrammene er skrevet i Mermaid, så GitHub viser dem direkte. De er tegnet ut fra koden slik
den er (`app/models/`, `app/controllers/`), og de skal oppdateres når domenet endres.

Kolonnen «Brukt» skiller mellom design som styrte arbeidet før koding, gjennom planene i
`docs/plans/`, og diagrammer som er tegnet etterpå for å dokumentere løsningen.

| Dokument | Innhold | Brukt |
|---|---|---|
| [brukerhistorier.md](brukerhistorier.md) | Én brukerhistorie per krav (A1–A4, C1–C5) og tillegg | **Før koding:** første del av hver plan (fase 3–8). Hver funksjon ble bygget og testet mot sin historie |
| [ordrestatus.md](ordrestatus.md) | Tilstandsmaskin for ordrestatus | **Før koding:** skissert i plan 01 og 02 og implementert direkte som `ALLOWED_TRANSITIONS`. Testene går gjennom hver pil, og admin-siden viser bare lovlige knapper |
| [mvc.md](mvc.md) | MVC-arkitektur og lagregler | **Før koding:** mappestruktur og lagregler i plan 01 og `CLAUDE.md`. `tests/test_architecture.py` sjekker at bare repositories bruker SQLite. Diagrammet er tegnet etterpå |
| [domenemodell.md](domenemodell.md) | Klassediagram for domeneklassene | **Delvis før:** klassene og tabellene ble beskrevet i plan 01 og 02. Diagrammet er tegnet etterpå fra koden |
| [use-case.md](use-case.md) | Aktører (kunde, admin) og brukstilfeller | **Etterpå:** oppsummerer kravene og viser hvordan de fordeler seg på blueprintene |
| [grafmodell.md](grafmodell.md) | Grafdatamodell for Neo4j (Oblig 5): noder, relasjoner, mapping fra SQLite, eksempelspørringer og skjermbilder fra Neo4j Browser | **Før koding:** grafmodellen sto i plan 10 og ble implementert slik. Etterpå bekreftet med `db.schema.visualization()` og 12 strukturkontroller |
| [bestilling-sekvens.md](bestilling-sekvens.md) | Sekvensdiagram for bestilling (C3) | **Etterpå:** dokumenterer to valg fra planene: kurven beholdes ved innlogging (plan 05), og ordren lagres i én transaksjon (plan 02) |
