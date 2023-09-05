import uuid
from datetime import datetime
from repository.reports.models import Report
from repository import db
from api.errors import InternalError, NotFoundError, BadRequest
from utils.logger import logger, stringify
from sqlalchemy.exc import ProgrammingError
from repository.query_builder import build_query, build_count
from sqlalchemy import and_, not_, select, text
from datetime import datetime, timedelta


def create_report(data):
    logger.repository(f"data: {stringify(data)}")
    try:
        today = datetime.today()
        report = Report(
            id=f"{uuid.uuid4()}",
            pet_id=data.get('pet_id'),
            notes=[],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            type=data.get("type"),
            place=data.get("place"),
            reporter=data.get("reporter"),
            responders=data.get("responders"),
            created_at=today.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        )
        db.session.add(report)
        db.session.commit()
        logger.check(f"report: {report}")
        return report.to_dict()
    except Exception as e:
        logger.error(e)
        raise BadRequest(e)


def update_report(id, data):
    logger.repository(
        f"id: {id}\n"
        f"dta: {stringify(data)}"
    )
    try:
        report_model = db.session.query(Report).filter(Report.id == id)
        if not report_model:
            raise NotFoundError(f"no report found with id: {id}")
        report_old = report_model.first().to_dict()
        report_model.update(data)
        db.session.commit()
        report = {**report_old, **report_model.first().to_dict()}
        logger.check(f'report: {stringify(report)}')
        return report
    except Exception as e:
        logger.error(e)
        raise e


def get_reports(common_search):
    logger.repository(f"commons_search: {stringify(common_search)}")
    try:
        query = build_query(table="reports", ordering=common_search["ordering"],
                            filters=common_search['filters'], pagination=common_search['pagination'])
        logger.check(f"query: {query}")
        manager = select(Report).from_statement(text(query))
        reports_model = db.session.execute(manager).scalars()
        reports = [report.to_dict() for report in reports_model]
        logger.check(f"reports found {len(reports)}")
        return reports
    except ProgrammingError as e:
        logger.error(e)
        exception = BadRequest(
            "The fields provided may contains syntax errors")
        exception.extension['extra'] = str(e)
        raise exception
    except Exception as e:
        logger.error(e)
        raise e


def get_report(id):
    logger.repository(f"id: {id}")
    try:
        report_model = Report.query.get(id)
        if not report_model:
            raise
        report = report_model.to_dict()
        logger.check(f"report: {stringify(report)}")
        return report
    except Exception as e:
        logger.error(e)
        raise e


def get_total_items(common_search):
    try:
        query = build_count(table="reports", filters=common_search['filters'])
        result = db.session.execute(query).first()
        return result[0] if result != None else 0
    except ProgrammingError as e:
        logger.error(e)
        raise BadRequest('malformed variables_fields')
    except Exception as e:
        logger.error(e)
        raise e

def get_all_reports ():
    logger.repository("fetching all users")
    try:
        users  = Report.query.all()
        logger.check(f"users: {len(users)}")
        return users
    except Exception as e:
        logger.error(e)
        raise e
    
def get_daily_reports():
    logger.repository('fetching all active users ')
    try: 
        users = db.session.query(Report).filter(
            and_( 
                 (Report.created_at> datetime.now() -timedelta(days=1) )
                ) 
            ).all()
        logger.check(f"active users: {len(users)}")
        return users
    except Exception as e:
        logger.error(e)
        raise e