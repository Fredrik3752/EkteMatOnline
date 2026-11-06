# Brukerhistorier

Rollene er hentet fra den syntetiske datapakken (Lab 7): eier, eventkoordinator,
kjøkkensjef og kunder (privat og bedrift).

## Kundeside

| Krav | Brukerhistorie | Akseptansekriterier (testet i `tests/`) |
|---|---|---|
| C1 | Som **kunde** vil jeg se rettene som kort gruppert etter type arrangement, slik at jeg raskt finner mat til mitt arrangement. | Bare publiserte retter vises. Kortet viser bilde, pris, minimum og allergener. Ukjent arrangement gir 404 (`test_menu.py`) |
| C2 | Som **kunde** vil jeg legge retter i en handlekurv, endre antall og se estimert total, slik at jeg kan sette sammen bestillingen. | Antall under minimum avvises, totalen stemmer, og avpubliserte retter fjernes (`test_cart.py`) |
| C3 | Som **kunde** vil jeg logge inn og sende bestillingen med dato, gjester, adresse og allergier per gjestegruppe, slik at kjøkkenet får alt i én bestilling. | Krever innlogging, og kurven overlever innloggingen. Datoen må være etter i dag. Gjestegruppene kan ikke ha flere gjester enn bestillingen (`test_checkout.py`) |
| C4 | Som **kunde** vil jeg se mine ordrer med status og betalingsstatus. | Bare egne ordrer vises. Avbestilling er lov bare mens ordren er sendt inn (`test_my_orders.py`) |
| C5 | Som **kunde** vil jeg spørre om en bestemt ordre og lese svaret, slik at jeg slipper e-post og telefon. | Bare om egne ordrer. Svaret vises på ordresiden (`test_questions.py`) |

## Administrasjon

| Krav | Brukerhistorie | Akseptansekriterier |
|---|---|---|
| A1 | Som **kjøkkensjef** vil jeg legge til, endre og fjerne retter og bestemme om de er publisert, slik at menyen er oppdatert. | Validering per felt. Slettede retter beholder navn og pris i gamle ordrer (`test_admin_food_items.py`) |
| A2 | Som **kjøkkensjef** vil jeg laste opp et bilde per rett og se det før det lagres. | Retten endres ikke før «Lagre bildet». Filtypen sjekkes på innholdet. Bare admin ser forhåndsvisningen (`test_images.py`) |
| A3 | Som **eventkoordinator** vil jeg filtrere ordrer på status og dato og endre ordre- og betalingsstatus, slik at jeg slipper Excel-arket. | Bare lovlige statusoverganger. Ugyldige filtre ignoreres med en melding (`test_admin_orders.py`) |
| A4 | Som **eventkoordinator** vil jeg se ubesvarte spørsmål først og svare direkte, slik at ingen henvendelser blir liggende. | Et besvart spørsmål kan ikke overskrives (`test_questions.py`) |

## Tillegg

| Behov fra datapakken | Brukerhistorie | Løsning |
|---|---|---|
| Eieren: vise hvor maten kommer fra | Som **eier** vil jeg at hvert kort viser opprinnelsen til råvarene. | Feltet `origin` på `FoodItem`, vist på kortet |
| GDPR-notatet: allergier er helseopplysninger | Som **Ekte Mat** vil vi lagre allergier per gjestegruppe, ikke per navngitt gjest. | `GuestGroup`, og skjemaet ber om at gjestene ikke navngis |
