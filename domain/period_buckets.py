"""Shared WEEKLY/MONTHLY/YEARLY bucketing for chart.js-ready trend data.
Used by domain/walk_stats and domain/pet_weights so both build their series
on the same label grid (same bucket count/keys per period)."""
from datetime import datetime, timedelta
from utils.dates import utc_now

WEEKLY = "WEEKLY"
MONTHLY = "MONTHLY"
YEARLY = "YEARLY"

WEEKLY_BUCKETS = 12
MONTHLY_BUCKETS = 12
YEARLY_BUCKETS = 5


def parse_dt(value):
    if isinstance(value, datetime):
        return value
    # to_dict() renders created_at via str(datetime), e.g. "2026-07-10 15:42:56.123456"
    value = value.split(".")[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"unrecognized datetime format: {value}")


def bucket_key(dt, period):
    if period == WEEKLY:
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    if period == MONTHLY:
        return f"{dt.year}-{dt.month:02d}"
    return f"{dt.year}"


def labels_for_period(period):
    now = utc_now()
    if period == WEEKLY:
        start = now - timedelta(weeks=WEEKLY_BUCKETS - 1)
        return [
            bucket_key(start + timedelta(weeks=i), WEEKLY)
            for i in range(WEEKLY_BUCKETS)
        ]
    if period == MONTHLY:
        labels = []
        y, m = now.year, now.month
        for i in range(MONTHLY_BUCKETS - 1, -1, -1):
            mm = m - i
            yy = y
            while mm <= 0:
                mm += 12
                yy -= 1
            labels.append(f"{yy}-{mm:02d}")
        return labels
    return [str(now.year - i) for i in range(YEARLY_BUCKETS - 1, -1, -1)]
