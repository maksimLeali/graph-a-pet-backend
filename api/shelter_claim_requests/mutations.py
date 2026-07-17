from ariadne import convert_kwargs_to_snake_case
import domain.shelter_claim_requests as claims_domain
from api.middlewares import auth_middleware
from api.authorization.decorators import require_permission
from domain.authorization.catalog import PlatformPermissions
from api.errors import format_error
from utils import get_request_user
from utils.logger import logger, stringify


def _ok(claim=None):
    return {"success": True, "shelter_claim_request": claim}


def _err(e, info):
    logger.error(e)
    return {
        "success": False,
        "error": format_error(e, info.context.headers['authorization']),
    }


@convert_kwargs_to_snake_case
@auth_middleware
def request_shelter_claim_resolver(obj, info, shelter_id, data=None):
    logger.api(f"shelter_id: {shelter_id} data: {stringify(data)}")
    try:
        me = get_request_user(info.context.headers['authorization'])
        claim = claims_domain.request_claim(shelter_id, data, me["id"])
        return _ok(claim)
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def cancel_shelter_claim_resolver(obj, info, id):
    logger.api(f"id: {id} cancel")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.cancel_claim(id, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CLAIMS_REVIEW, platform=True)
def approve_shelter_claim_resolver(obj, info, id, decision_note=None):
    logger.api(f"id: {id} approve")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.approve_claim(id, decision_note, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CLAIMS_REVIEW, platform=True)
def reject_shelter_claim_resolver(obj, info, id, decision_note=None):
    logger.api(f"id: {id} reject")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.reject_claim(id, decision_note, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@auth_middleware
def update_shelter_claim_documents_resolver(obj, info, id, documents):
    logger.api(f"id: {id} update documents")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.update_claim_documents(id, documents, me["id"]))
    except Exception as e:
        return _err(e, info)


@convert_kwargs_to_snake_case
@require_permission(PlatformPermissions.CLAIMS_REVIEW, platform=True)
def request_shelter_claim_document_change_resolver(obj, info, id, document_id, note=None):
    logger.api(f"id: {id} document: {document_id} request change")
    try:
        me = get_request_user(info.context.headers['authorization'])
        return _ok(claims_domain.request_document_change(id, document_id, note, me["id"]))
    except Exception as e:
        return _err(e, info)
