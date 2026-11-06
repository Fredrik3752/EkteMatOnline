"""Jinja filters for presenting stored values. Timestamps are stored in UTC (SQLite CURRENT_TIMESTAMP)."""
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover – Python < 3.9
    ZoneInfo = None

DEFAULT_TIMEZONE = "Europe/Oslo"


def local_time(value, tz_name=DEFAULT_TIMEZONE):
    """'2026-11-06 02:35:38' (UTC) -> '06.11.2026 kl. 03:35' (Norwegian time)."""
    if not value:
        return ""
    try:
        moment = datetime.strptime(str(value)[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if ZoneInfo is not None:
            moment = moment.astimezone(ZoneInfo(tz_name))
    except (ValueError, KeyError, OSError):
        return str(value)
    return moment.strftime("%d.%m.%Y kl. %H:%M")


def register_filters(app):
    from app.models.money import format_nok, ore_to_input

    tz_name = app.config.get("TIMEZONE", DEFAULT_TIMEZONE)
    app.jinja_env.filters["nok"] = format_nok
    app.jinja_env.filters["nok_input"] = ore_to_input
    app.jinja_env.filters["local_time"] = lambda value: local_time(value, tz_name)
