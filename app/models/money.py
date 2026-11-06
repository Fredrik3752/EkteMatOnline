"""Money helpers. Amounts are integer øre (100 øre = 1 NOK)."""


def format_nok(amount_ore: int) -> str:
    """Format øre as Norwegian kroner, e.g. 189000 -> '1 890,00 kr'."""
    sign = "-" if amount_ore < 0 else ""
    kroner, ore = divmod(abs(int(amount_ore)), 100)
    grouped = f"{kroner:,}".replace(",", " ")  # non-breaking space as thousands separator
    return f"{sign}{grouped},{ore:02d} kr"


def nok_to_ore(value) -> int:
    """Parse a user-entered NOK amount ('189', '189,50', '1 890.5') to øre."""
    text = str(value).strip().replace(" ", "").replace(" ", "").replace(",", ".")
    if not text:
        raise ValueError("empty amount")
    kroner, _, fraction = text.partition(".")
    if not kroner.lstrip("-").isdigit() or (fraction and not fraction.isdigit()) or len(fraction) > 2:
        raise ValueError(f"invalid amount: {value!r}")
    ore = int(kroner) * 100 + int((fraction or "0").ljust(2, "0"))
    if ore < 0:
        raise ValueError("amount cannot be negative")
    return ore


def ore_to_input(amount_ore: int) -> str:
    """Øre as an editable NOK value: 18900 -> '189', 18950 -> '189,50'."""
    kroner, ore = divmod(int(amount_ore), 100)
    return f"{kroner}" if ore == 0 else f"{kroner},{ore:02d}"
