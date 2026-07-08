import uuid
from datetime import datetime, timedelta

from repository import db
from repository.shelter_dashboard_snapshots.models import ShelterKpiSnapshot, KPI_FIELDS
from utils.logger import logger, stringify


def upsert_snapshot(shelter_id, snapshot_date, kpis):
    """Crea/aggiorna la riga KPI del giorno per lo shelter (idempotente)."""
    logger.repository(f"snapshot {shelter_id} @ {snapshot_date}")
    try:
        row = db.session.query(ShelterKpiSnapshot).filter(
            ShelterKpiSnapshot.shelter_id == shelter_id,
            ShelterKpiSnapshot.snapshot_date == snapshot_date,
        ).first()
        values = {f: kpis.get(f, 0) for f in KPI_FIELDS}
        if row is None:
            row = ShelterKpiSnapshot(
                id=f"{uuid.uuid4()}",
                created_at=datetime.today().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                shelter_id=shelter_id,
                snapshot_date=snapshot_date,
                **values,
            )
            db.session.add(row)
        else:
            for f, v in values.items():
                setattr(row, f, v)
            row.updated_at = datetime.today().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        db.session.commit()
        return row.to_dict()
    except Exception as e:
        db.session.rollback()
        logger.error(e)
        raise e


def get_history(shelter_id, from_date, to_date):
    logger.repository(f"kpi history {shelter_id} {from_date}..{to_date}")
    try:
        rows = db.session.query(ShelterKpiSnapshot).filter(
            ShelterKpiSnapshot.shelter_id == shelter_id,
            ShelterKpiSnapshot.snapshot_date >= from_date,
            ShelterKpiSnapshot.snapshot_date <= to_date,
        ).order_by(ShelterKpiSnapshot.snapshot_date.asc()).all()
        return [r.to_dict() for r in rows]
    except Exception as e:
        logger.error(e)
        raise e
