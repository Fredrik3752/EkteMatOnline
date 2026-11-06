"""Friendly error pages."""
from flask import render_template

MESSAGES = {
    400: ("Ugyldig forespørsel", "Forespørselen kunne ikke behandles."),
    403: ("Ingen tilgang", "Du har ikke tilgang til denne siden."),
    404: ("Fant ikke siden", "Siden du leter etter finnes ikke."),
    413: ("Filen er for stor", "Filen du prøvde å laste opp er for stor. Bilder kan være høyst 5 MB."),
}


def register_error_handlers(app):
    for code in MESSAGES:
        app.register_error_handler(code, _handler(code))


def _handler(code):
    def handle(error):
        title, default_text = MESSAGES[code]
        description = getattr(error, "description", None)
        # Werkzeug's default English descriptions are replaced by our Norwegian text.
        text = description if description and not description.startswith(("The ", "You ")) else default_text
        return render_template("errors/error.html", code=code, title=title, text=text), code
    return handle
