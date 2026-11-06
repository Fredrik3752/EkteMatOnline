# Sekvensdiagram: kunden sender en bestilling (C3)

Viser flyten fra «Gå til bestilling» i handlekurven til kvitteringen, inkludert innlogging
midt i flyten.

```mermaid
sequenceDiagram
    autonumber
    actor K as Kunde (nettleser)
    participant CO as checkout.py<br/>(Controller)
    participant AU as account.py / auth.py<br/>(Controller)
    participant CA as Cart<br/>(Model)
    participant O as Order<br/>(Model)
    participant FR as FoodItemRepository
    participant OR as OrderRepository
    participant DB as SQLite

    K->>CO: GET /bestilling
    CO-->>K: 302 → /logg-inn?next=/bestilling (ikke innlogget)
    K->>AU: POST /logg-inn (e-post, passord, CSRF)
    AU->>AU: log_in(): tøm session, behold handlekurven
    AU-->>K: 302 → /bestilling

    K->>CO: GET /bestilling
    CO->>FR: get_many(item_ids fra session)
    FR->>DB: SELECT food_items + koblinger
    FR-->>CO: FoodItem-objekter
    CO->>CA: Cart.build(antall, retter)
    CA-->>CO: kurv (fjerner avpubliserte), problems()
    CO-->>K: skjema + oppsummering

    K->>CO: POST /bestilling (dato, gjester, adresse, gjestegrupper)
    CO->>CA: to_order_lines() – kopier navn og pris
    CO->>O: Order(...).validate(today)
    alt ugyldig
        O-->>CO: ValidationError
        CO-->>K: 400 + feil per felt (kurven beholdes)
    else gyldig
        CO->>OR: add(order)
        OR->>DB: BEGIN, INSERT orders, order_lines, guest_groups, COMMIT
        OR-->>CO: lagret Order (status = submitted)
        CO->>CO: clear_cart()
        CO-->>K: 302 → /bestilling/{id}/kvittering
    end
```

Diagrammet er tegnet etter at koden var skrevet. Det viser to valg som ble tatt i plan 05 og plan 02:
- Innlogging tømmer sessionen for å hindre session fixation. Uten unntak ville kunden mistet
  handlekurven i trinn 4, så `log_in()` beholder den.
- Ordre, linjer og gjestegrupper lagres i **én transaksjon**, slik at en halv ordre aldri blir
  liggende i databasen (`test_order_with_invalid_line_rolls_back`).
