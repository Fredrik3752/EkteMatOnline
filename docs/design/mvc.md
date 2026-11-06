# MVC-arkitektur

```mermaid
flowchart TB
    Browser(["Nettleser"])

    subgraph C["Controller – app/controllers/ (Flask-blueprints)"]
        shop["shop<br/>/ , /meny"]
        cart["cart<br/>/handlekurv"]
        checkout["checkout<br/>/bestilling"]
        account["account<br/>/registrer, /logg-inn, /mine-ordrer"]
        admin["admin<br/>/admin/…"]
        cross["auth · csrf · errors · formatting"]
    end

    subgraph V["View – app/templates/ (Jinja2)"]
        tpl["base.html · shop/ · cart/ · checkout/<br/>account/ · admin/ · orders/_details.html"]
    end

    subgraph M["Model – app/models/"]
        domain["Domeneklasser og regler<br/>FoodItem · Order · OrderStatus · Cart<br/>GuestGroup · Question · User · image"]
        subgraph R["repositories/ – eneste kode som rører lagring"]
            repos["Offentlige navn + kontrakter (base.py)<br/>UserRepository · FoodItemRepository<br/>OrderRepository · QuestionRepository · …"]
            sqlite["sqlite/<br/>Sqlite*Repository"]
            neo["neo4j/<br/>Neo4j*Repository (Cypher)"]
            store["ImageStore"]
        end
    end

    DB[("SQLite<br/>instance/ektemat.db")]
    Files[("Bildefiler<br/>static/uploads/food<br/>instance/image_previews")]
    Neo[("Neo4j 5.26<br/>Docker")]

    Browser -- "HTTP" --> C
    C -- "render_template(domeneobjekter)" --> V
    V -- "HTML" --> Browser
    C -- "kaller regler" --> domain
    C -- "henter/lagrer" --> repos
    C --> store
    repos -- "returnerer domeneobjekter" --> C
    repos -- "STORAGE_BACKEND=sqlite" --> sqlite
    repos -- "STORAGE_BACKEND=neo4j" --> neo
    sqlite -- "SQL" --> DB
    neo -- "Cypher (Bolt)" --> Neo
    store --> Files
```

## Regler mellom lagene

| Regel | Hvorfor | Sjekket av |
|---|---|---|
| Bare `repositories/sqlite/` bruker SQLite, og bare `repositories/neo4j/` bruker Neo4j | Lagringen kan byttes uten endringer i controllere og views. Det skjedde i Oblig 5: `git diff oblig4 -- app/controllers app/templates` er tom | `tests/test_architecture.py` |
| Controllerne importerer bare de offentlige navnene (`FoodItemRepository` …), aldri en bestemt lagring | `backend.py` velger implementasjon ut fra `STORAGE_BACKEND` | `tests/test_architecture.py`, `tests/test_storage_backend.py` |
| Begge lagringene oppfyller de samme kontraktene (`base.py`) | Samme oppførsel uansett lagring | Kontrakttestene i `tests/test_repositories.py` (mot begge) |
| Repositories returnerer domeneobjekter, aldri `sqlite3.Row` | Viewene er uavhengige av lagringen | Kodegjennomgang og repository-testene |
| Forretningsregler ligger i domeneklassene, ikke i controllerne | Reglene kan testes uten Flask (`tests/test_domain.py`, `tests/test_cart.py`) | `Order.change_status`, `Cart.problems`, `check_quantity` |
| Controllerne er tynne: de leser forespørselen, kaller modellen og velger view | Lett å lese og teste | Rutetestene |
| Handlekurven ligger i Flask-session, ikke i databasen | Den er nettleserdata og ikke forretningsdata. Den blir en ordre ved bestilling | `app/controllers/cart.py` |
