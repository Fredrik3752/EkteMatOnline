# Skjermbilder

Tatt 2026-11-06 med syntetiske seed-data, i et nettleservindu på 1280 × 860 som er skalert ned
til 800 px bredde. Bildene på menykortene er testbilder lastet opp gjennom A2-funksjonen.
Alle personer, ordrer og adresser er oppdiktet.

## Kundeside

| Fil | Side | Krav |
|---|---|---|
| [01-meny.jpg](01-meny.jpg) | Meny for bryllup: kort med bilde, pris, minimum, allergener og opprinnelse | C1 |
| [02-handlekurv.jpg](02-handlekurv.jpg) | Handlekurv med antall, linjesummer og estimert total | C2 |
| [03-bestilling.jpg](03-bestilling.jpg) | Bestillingsskjema med dato, gjester, adresse og gjestegrupper | C3 |
| [04-mine-ordrer.jpg](04-mine-ordrer.jpg) | Mine ordrer med ordrestatus og betalingsstatus | C4 |
| [05-sporsmal.jpg](05-sporsmal.jpg) | Spørsmål om en ordre, med svar fra Ekte Mat og skjema for nytt spørsmål | C5 |

## Administrasjon

| Fil | Side | Krav |
|---|---|---|
| [06-admin-matretter.jpg](06-admin-matretter.jpg) | Liste over matretter med miniatyrbilder og handlinger | A1 |
| [07-admin-matrett-skjema.jpg](07-admin-matrett-skjema.jpg) | Redigere matrett: pris, minimum, arrangementer og allergener | A1 |
| [08-admin-bilde-forhandsvisning.jpg](08-admin-bilde-forhandsvisning.jpg) | Bilde forhåndsvist før lagring: nåværende, nytt og menykort | A2 |
| [09-admin-ordreliste.jpg](09-admin-ordreliste.jpg) | Ordreliste med filter på status og eventdato | A3 |
| [10-admin-ordre.jpg](10-admin-ordre.jpg) | Ordreside med lovlige statusknapper og betalingsstatus | A3 |
| [11-admin-sporsmal.jpg](11-admin-sporsmal.jpg) | Ubesvarte spørsmål med svarskjema | A4 |

## Neo4j (Oblig 5)

Tatt i Neo4j Browser (http://localhost:7474) mot utviklingsdatabasen etter nettlesertesten i fase N4.

| Fil | Innhold |
|---|---|
| [12-neo4j-ordre-graf.jpg](12-neo4j-ordre-graf.jpg) | Ordre 5 som graf: kunde, ordre, ordrelinjer → retter, gjestegrupper, spørsmål med svar fra admin |
| [13-neo4j-skjema.jpg](13-neo4j-skjema.jpg) | `CALL db.schema.visualization()`: 11 node-typer og 10 relasjonstyper |
