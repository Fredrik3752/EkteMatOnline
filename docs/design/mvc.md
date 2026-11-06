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
            repos["UserRepository · FoodItemRepository<br/>OrderRepository · QuestionRepository<br/>EventCategory-/Allergen-/DietaryLabelRepository"]
            store["ImageStore"]
        end
    end

    DB[("SQLite<br/>instance/ektemat.db")]
    Files[("Bildefiler<br/>static/uploads/food<br/>instance/image_previews")]
    Neo[("Neo4j – oblig 5")]

    Browser -- "HTTP" --> C
    C -- "render_template(domeneobjekter)" --> V
    V -- "HTML" --> Browser
    C -- "kaller regler" --> domain
    C -- "henter/lagrer" --> repos
    C --> store
    repos -- "returnerer domeneobjekter" --> C
    repos -- "SQL" --> DB
    store --> Files
    repos -. "kan byttes ut" .-> Neo
```

## Regler mellom lagene

| Regel | Hvorfor | Sjekket av |
|---|---|---|
| Bare `app/models/repositories/` importerer `sqlite3` eller skriver SQL | Neo4j skal kunne erstatte SQLite uten endringer i controllere og views | `tests/test_architecture.py` |
| Repositories returnerer domeneobjekter, aldri `sqlite3.Row` | Viewene er uavhengige av lagringen | Kodegjennomgang og repository-testene |
| Forretningsregler ligger i domeneklassene, ikke i controllerne | Reglene kan testes uten Flask (`tests/test_domain.py`, `tests/test_cart.py`) | `Order.change_status`, `Cart.problems`, `check_quantity` |
| Controllerne er tynne: de leser forespørselen, kaller modellen og velger view | Lett å lese og teste | Rutetestene |
| Handlekurven ligger i Flask-session, ikke i databasen | Den er nettleserdata og ikke forretningsdata. Den blir en ordre ved bestilling | `app/controllers/cart.py` |
