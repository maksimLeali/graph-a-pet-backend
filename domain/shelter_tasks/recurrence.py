"""Ricorrenze delle shelter task.

La ricorrenza è persistita in colonne strutturate su `shelter_tasks`:
    recurrence_freq      DAILY | WEEKLY | MONTHLY
    recurrence_interval  ogni N (giorni/settimane/mesi)
    recurrence_weekdays  WEEKLY: giorni; MONTHLY: giorno-settimana target (lista)
    recurrence_week_ordinal  MONTHLY: 1..5 = primo..quinto, -1 = ultimo
    recurrence_time      "HH:MM"
    recurrence_start     data inizio (ancora per interval)

Esempi:
    "ogni settimana il sabato"   -> WEEKLY, [SAT], interval 1
    "ogni mese il primo mercoledì" -> MONTHLY, [WED], week_ordinal 1
"""
from datetime import datetime, date, timedelta
from calendar import monthrange

from api.errors import BadRequest

DATE_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"

WEEKDAYS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


# --- RecurrenceInput (GraphQL) -> colonne persistite ---
def apply_to_data(data):
    """Se `data` contiene `recurrence`, la mappa sulle colonne strutturate +
    is_recurring + scheduled_at (per display). Muta e ritorna data."""
    rec = data.pop("recurrence", None)
    if rec is None:
        return data

    freq = (rec.get("freq") or "").upper()
    if freq not in ("DAILY", "WEEKLY", "MONTHLY"):
        raise BadRequest(f"unsupported recurrence freq: {freq}")
    weekdays = [w.upper() for w in (rec.get("weekdays") or []) if w.upper() in WEEKDAYS]
    if freq == "WEEKLY" and not weekdays:
        raise BadRequest("WEEKLY recurrence requires at least one weekday")
    if freq == "MONTHLY" and not weekdays:
        raise BadRequest("MONTHLY recurrence requires a weekday")

    start_at = rec.get("start_at")
    start_dt = None
    if start_at:
        try:
            start_dt = datetime.strptime(start_at, DATE_FMT)
        except Exception:
            try:
                start_dt = datetime.strptime(start_at[:10], "%Y-%m-%d")
            except Exception:
                start_dt = None
    if start_dt is None:
        start_dt = datetime.today()

    tod = rec.get("time_of_day")
    if tod:
        try:
            h, m = tod.split(":")
            start_dt = start_dt.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
        except Exception:
            tod = None

    data["is_recurring"] = True
    data["recurrence_freq"] = freq
    data["recurrence_interval"] = rec.get("interval") or 1
    data["recurrence_weekdays"] = weekdays or None
    data["recurrence_week_ordinal"] = rec.get("week_ordinal") if freq == "MONTHLY" else None
    data["recurrence_time"] = tod
    data["recurrence_start"] = start_dt.strftime(DATE_FMT)
    # scheduled_at come ancora/display (inizio + ora)
    data["scheduled_at"] = start_dt.strftime(DATE_FMT)
    return data


# --- colonne -> Recurrence (campo GraphQL) ---
def build(tpl):
    if not tpl.get("recurrence_freq"):
        return None
    return {
        "freq": tpl["recurrence_freq"],
        "interval": tpl.get("recurrence_interval") or 1,
        "weekdays": tpl.get("recurrence_weekdays"),
        "week_ordinal": tpl.get("recurrence_week_ordinal"),
        "time_of_day": tpl.get("recurrence_time"),
        "start_at": tpl.get("recurrence_start"),
    }


# --- calcolo occorrenze ---
def _anchor_date(tpl):
    v = tpl.get("recurrence_start") or tpl.get("scheduled_at") or tpl.get("created_at")
    if not v:
        return None
    try:
        return datetime.strptime(v, DATE_FMT).date()
    except Exception:
        return None


def rule_time(tpl):
    """(hour, minute) dell'occorrenza."""
    tod = tpl.get("recurrence_time")
    if tod:
        try:
            h, m = tod.split(":")
            return (int(h), int(m))
        except Exception:
            pass
    v = tpl.get("recurrence_start") or tpl.get("scheduled_at")
    if v:
        try:
            dtp = datetime.strptime(v, DATE_FMT)
            return (dtp.hour, dtp.minute)
        except Exception:
            pass
    return (0, 0)


def _monday(d):
    return d - timedelta(days=d.weekday())


def nth_weekday_of_month(year, month, weekday, ordinal):
    if ordinal > 0:
        first = date(year, month, 1)
        offset = (weekday - first.weekday()) % 7
        day = 1 + offset + (ordinal - 1) * 7
        if day > monthrange(year, month)[1]:
            return None
        return date(year, month, day)
    ndays = monthrange(year, month)[1]
    last = date(year, month, ndays)
    offset = (last.weekday() - weekday) % 7
    return date(year, month, ndays - offset)


def occurs_on(tpl, day):
    """True se il template ricorre nella data `day` (datetime.date)."""
    freq = (tpl.get("recurrence_freq") or "").upper()
    if not freq:
        return False
    anchor = _anchor_date(tpl)
    if anchor and day < anchor:
        return False
    interval = tpl.get("recurrence_interval") or 1
    weekdays = tpl.get("recurrence_weekdays") or []

    if freq == "DAILY":
        if interval <= 1 or not anchor:
            return True
        return (day - anchor).days % interval == 0

    if freq == "WEEKLY":
        wanted = [WEEKDAYS[d] for d in weekdays if d in WEEKDAYS]
        if day.weekday() not in wanted:
            return False
        if interval <= 1 or not anchor:
            return True
        weeks = (_monday(day) - _monday(anchor)).days // 7
        return weeks % interval == 0

    if freq == "MONTHLY":
        wd = weekdays[0] if weekdays else None
        if wd not in WEEKDAYS:
            return False
        ordinal = tpl.get("recurrence_week_ordinal") or 1
        target = nth_weekday_of_month(day.year, day.month, WEEKDAYS[wd], ordinal)
        if target is None or target != day:
            return False
        if interval <= 1 or not anchor:
            return True
        months = (day.year - anchor.year) * 12 + (day.month - anchor.month)
        return months % interval == 0

    return False
