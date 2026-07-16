"""Single source of truth for "now" in the backend.

Convention: the DB stores naive datetimes that are ALWAYS UTC
(columns are db.DateTime without timezone). Every piece of code that
needs the current time must call utc_now() — never datetime.now() /
datetime.today(), which return server-local time and silently corrupt
timestamps when the host is not on UTC. The frontend receives ISO
strings with a "Z" suffix and is responsible for converting to the
viewer's local timezone.
"""
from datetime import datetime, timezone

ISO_Z_FMT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> datetime:
	"""Current UTC time as a naive datetime (storage convention)."""
	return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_iso() -> str:
	"""Current UTC time as an ISO-8601 string with a Z suffix."""
	return utc_now().strftime(ISO_Z_FMT)


def iso_z(value):
	"""Serialize a stored datetime/date for the API.

	Naive datetimes are UTC by convention, so they get an explicit "Z"
	suffix — without it the frontend (dayjs/Date) would parse the string
	as viewer-local time. Plain dates (no time component, e.g. birthday)
	stay date-only. None passes through, and non-date values fall back to
	str() so callers can use this everywhere they used str() before.
	"""
	if value is None:
		return None
	if isinstance(value, datetime):
		return value.strftime(ISO_Z_FMT)
	return str(value)
