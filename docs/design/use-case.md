# Use case-diagram

Mermaid har ingen egen diagramtype for use case. Diagrammet er derfor tegnet som en graf,
med aktørene til venstre og systemgrensen som en boks.

```mermaid
flowchart LR
    Kunde(["👤 Kunde"])
    Admin(["👤 Ekte Mat-ansatt (admin)"])

    subgraph System["Ekte Mat Online"]
        direction TB
        UC1(["C1 Se meny per arrangement"])
        UC2(["C2 Administrere handlekurv"])
        UC3(["C3 Sende bestilling"])
        UCR(["Registrere seg / logge inn"])
        UC4(["C4 Se mine ordrer"])
        UC4b(["Avbestille ordre"])
        UC5(["C5 Stille spørsmål om ordre"])

        UA1(["A1 Administrere matretter"])
        UA2(["A2 Laste opp og forhåndsvise bilde"])
        UA3(["A3 Behandle ordrer"])
        UA4(["A4 Svare på spørsmål"])
    end

    Kunde --- UC1
    Kunde --- UC2
    Kunde --- UC3
    Kunde --- UC4
    Kunde --- UC5
    UC3 -. "«include»" .-> UCR
    UC4b -. "«extend»" .-> UC4

    Admin --- UA1
    Admin --- UA2
    Admin --- UA3
    Admin --- UA4
    UA2 -. "«extend»" .-> UA1
```

- **Kunde:** besøkende kan se menyen og fylle handlekurven uten å logge inn. Bestilling,
  mine ordrer og spørsmål krever innlogging.
- **Admin:** alle admin-brukstilfellene krever rollen `admin`, som `@admin_required` sjekker.
