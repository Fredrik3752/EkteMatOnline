# Domenemodell (klassediagram)

Klassene finnes i `app/models/`. Priser er i øre (heltall). `Cart` lagres ikke i databasen,
men i sessionen, og gjøres om til `OrderLine`-er ved bestilling.

```mermaid
classDiagram
    direction LR

    class User {
        +int id
        +str email
        +str name
        +str phone
        +str role  "customer | admin"
        +str password_hash
        +create(email, name, password)$ User
        +check_password(pw) bool
        +is_admin bool
    }

    class EventCategory {
        +int id
        +str slug
        +str name
        +int sort_order
    }
    class Allergen {
        +int id
        +str code
        +str name
    }
    class DietaryLabel {
        +int id
        +str code
        +str name
    }

    class FoodItem {
        +int id
        +str name
        +str description
        +int price_ore
        +int min_order_qty
        +bool is_published
        +str image_path
        +str origin
        +accepts_quantity(qty) bool
        +validate()
    }

    class Cart {
        +build(quantities, items)$ Cart
        +total_ore int
        +problems() list
        +to_order_lines() list~OrderLine~
    }
    class CartLine {
        +int quantity
        +line_total_ore int
        +meets_minimum bool
    }

    class Order {
        +int id
        +date event_date
        +int guest_count
        +str delivery_address
        +str notes
        +OrderStatus status
        +PaymentStatus payment_status
        +total_ore int
        +change_status(new)
        +change_payment_status(new)
        +can_be_cancelled_by_customer bool
        +validate(today)
    }
    class OrderLine {
        +str item_name
        +int quantity
        +int unit_price_ore
        +line_total_ore int
    }
    class GuestGroup {
        +str description
        +int guest_count
        +str allergy_notes
        +str dietary_notes
    }
    class Question {
        +int id
        +str body
        +str answer
        +str answered_at
        +is_answered bool
        +give_answer(text, admin_id)
    }

    class OrderStatus {
        <<enumeration>>
        SUBMITTED
        APPROVED
        IN_PREPARATION
        DELIVERED
        REJECTED
        CANCELLED
    }
    class PaymentStatus {
        <<enumeration>>
        NOT_PAID
        DEPOSIT_PAID
        INVOICED
        PAID
    }

    FoodItem "*" --> "1..*" EventCategory : passer for
    FoodItem "*" --> "*" Allergen : inneholder
    FoodItem "*" --> "*" DietaryLabel : merket

    Cart "1" *-- "*" CartLine
    CartLine "*" --> "1" FoodItem

    User "1" <-- "*" Order : customer
    Order "1" *-- "1..*" OrderLine
    Order "1" *-- "1..*" GuestGroup
    OrderLine "*" ..> "0..1" FoodItem : food_item_id (kopi av navn og pris)
    Order --> OrderStatus
    Order --> PaymentStatus

    Order "1" *-- "*" Question
    Question "*" --> "1" User : author
    Question "*" --> "0..1" User : answered_by
```

## Valg som diagrammet viser

- `OrderLine` **kopierer** navn og pris. Når admin endrer eller sletter en rett, endres ikke
  eksisterende ordrer (`food_item_id` blir `NULL` ved sletting).
- `GuestGroup` holder allergier per gruppe og ikke per navngitt gjest (GDPR art. 9 i datapakken).
- Ordrestatus og betalingsstatus er **uavhengige**. Ordrestatus følger tilstandsmaskinen i
  [ordrestatus.md](ordrestatus.md), mens betalingsstatus kan settes fritt av admin.
