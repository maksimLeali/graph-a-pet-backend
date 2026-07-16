from utils.logger import logger
from utils.telegram import send_message_to_admin
from utils import get_request_user
from config import cfg

# Machine-readable error codes shared by backend, GraphQL and frontend.
# HTTP status stays in `extension["code"]`; the string code goes in
# `extension["error_code"]` so existing consumers keep working (additive).
class ErrorCode:
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL = "INTERNAL"
    BOX_FULL = "BOX_FULL"
    BOX_OUT_OF_SERVICE = "BOX_OUT_OF_SERVICE"
    PET_ALREADY_ASSIGNED = "PET_ALREADY_ASSIGNED"
    PET_NOT_ASSIGNED = "PET_NOT_ASSIGNED"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    DUPLICATE_TASK_INSTANCE = "DUPLICATE_TASK_INSTANCE"
    INVALID_RECURRENCE_RULE = "INVALID_RECURRENCE_RULE"
    CANNOT_DELETE_WITH_ACTIVE_OCCUPANCY = "CANNOT_DELETE_WITH_ACTIVE_OCCUPANCY"
    CANNOT_DELETE_WITH_HISTORY = "CANNOT_DELETE_WITH_HISTORY"
    INVALID_AUTHORIZATION_SCOPE = "INVALID_AUTHORIZATION_SCOPE"
    MEMBERSHIP_NOT_ACTIVE = "MEMBERSHIP_NOT_ACTIVE"
    ROLE_NOT_ASSIGNABLE = "ROLE_NOT_ASSIGNABLE"
    ROLE_SCOPE_MISMATCH = "ROLE_SCOPE_MISMATCH"
    PERMISSION_ESCALATION_NOT_ALLOWED = "PERMISSION_ESCALATION_NOT_ALLOWED"
    LAST_ADMIN_CANNOT_BE_REMOVED = "LAST_ADMIN_CANNOT_BE_REMOVED"

    # donations
    DONATION_EXCEEDS_PET_LIMIT = "DONATION_EXCEEDS_PET_LIMIT"
    SHELTER_NOT_VERIFIED = "SHELTER_NOT_VERIFIED"
    SHELTER_DONATIONS_DISABLED = "SHELTER_DONATIONS_DISABLED"
    PET_NOT_PUBLISHED = "PET_NOT_PUBLISHED"
    STRIPE_CHARGES_NOT_ENABLED = "STRIPE_CHARGES_NOT_ENABLED"
    STRIPE_TEST_MODE_VIOLATION = "STRIPE_TEST_MODE_VIOLATION"
    INVALID_DONATION_AMOUNT = "INVALID_DONATION_AMOUNT"
    FUNDING_NEED_CLOSED = "FUNDING_NEED_CLOSED"
    DONATION_EXCEEDS_FUNDING_NEED_GOAL = "DONATION_EXCEEDS_FUNDING_NEED_GOAL"
    EXPENSE_NOT_EDITABLE = "EXPENSE_NOT_EDITABLE"
    RATE_LIMITED = "RATE_LIMITED"
    DUPLICATE_WEBHOOK_EVENT = "DUPLICATE_WEBHOOK_EVENT"


class BadRequest(Exception):
    extension = {"code": 400, "error_code": ErrorCode.VALIDATION_ERROR, "extra": None}

class AuthenticationError(Exception):
    extension = {"code": 401, "error_code": ErrorCode.UNAUTHORIZED, "extra": None}

class ForbiddenError(Exception):
    extension = {"code": 403, "error_code": ErrorCode.FORBIDDEN, "extra": None}

class NotFoundError(Exception):
    extension = {"code": 404, "error_code": ErrorCode.NOT_FOUND, "extra": None}

class InternalError(Exception):
    extension = {"code": 500, "error_code": ErrorCode.INTERNAL, "extra": None}


class DomainError(Exception):
    """Business-rule violation with a machine-readable code (HTTP 409/422 class).
    Subclasses set `error_code`; instances may override via constructor."""
    http_status = 422
    error_code = ErrorCode.VALIDATION_ERROR

    def __init__(self, message="", error_code=None, extra=None):
        super().__init__(message)
        code = error_code or self.error_code
        self.extension = {"code": self.http_status, "error_code": code, "extra": extra}


class BoxFullError(DomainError):
    http_status = 409
    error_code = ErrorCode.BOX_FULL

class BoxOutOfServiceError(DomainError):
    http_status = 409
    error_code = ErrorCode.BOX_OUT_OF_SERVICE

class PetAlreadyAssignedError(DomainError):
    http_status = 409
    error_code = ErrorCode.PET_ALREADY_ASSIGNED

class PetNotAssignedError(DomainError):
    http_status = 409
    error_code = ErrorCode.PET_NOT_ASSIGNED

class InsufficientStockError(DomainError):
    http_status = 409
    error_code = ErrorCode.INSUFFICIENT_STOCK

class DuplicateTaskInstanceError(DomainError):
    http_status = 409
    error_code = ErrorCode.DUPLICATE_TASK_INSTANCE

class InvalidRecurrenceRuleError(DomainError):
    http_status = 422
    error_code = ErrorCode.INVALID_RECURRENCE_RULE

class CannotDeleteWithActiveOccupancyError(DomainError):
    http_status = 409
    error_code = ErrorCode.CANNOT_DELETE_WITH_ACTIVE_OCCUPANCY

class CannotDeleteWithHistoryError(DomainError):
    http_status = 409
    error_code = ErrorCode.CANNOT_DELETE_WITH_HISTORY


class InvalidAuthorizationScopeError(DomainError):
    http_status = 400
    error_code = ErrorCode.INVALID_AUTHORIZATION_SCOPE

class MembershipNotActiveError(DomainError):
    http_status = 403
    error_code = ErrorCode.MEMBERSHIP_NOT_ACTIVE

class RoleNotAssignableError(DomainError):
    http_status = 409
    error_code = ErrorCode.ROLE_NOT_ASSIGNABLE

class RoleScopeMismatchError(DomainError):
    http_status = 409
    error_code = ErrorCode.ROLE_SCOPE_MISMATCH

class PermissionEscalationNotAllowedError(DomainError):
    http_status = 403
    error_code = ErrorCode.PERMISSION_ESCALATION_NOT_ALLOWED

class LastAdminCannotBeRemovedError(DomainError):
    http_status = 409
    error_code = ErrorCode.LAST_ADMIN_CANNOT_BE_REMOVED


class DonationExceedsPetLimitError(DomainError):
    http_status = 409
    error_code = ErrorCode.DONATION_EXCEEDS_PET_LIMIT

class ShelterNotVerifiedError(DomainError):
    http_status = 403
    error_code = ErrorCode.SHELTER_NOT_VERIFIED

class ShelterDonationsDisabledError(DomainError):
    http_status = 403
    error_code = ErrorCode.SHELTER_DONATIONS_DISABLED

class PetNotPublishedError(DomainError):
    http_status = 403
    error_code = ErrorCode.PET_NOT_PUBLISHED

class StripeChargesNotEnabledError(DomainError):
    http_status = 409
    error_code = ErrorCode.STRIPE_CHARGES_NOT_ENABLED

class StripeTestModeViolationError(DomainError):
    http_status = 403
    error_code = ErrorCode.STRIPE_TEST_MODE_VIOLATION

class InvalidDonationAmountError(DomainError):
    http_status = 422
    error_code = ErrorCode.INVALID_DONATION_AMOUNT

class FundingNeedClosedError(DomainError):
    http_status = 409
    error_code = ErrorCode.FUNDING_NEED_CLOSED

class DonationExceedsFundingNeedGoalError(DomainError):
    http_status = 409
    error_code = ErrorCode.DONATION_EXCEEDS_FUNDING_NEED_GOAL

class ExpenseNotEditableError(DomainError):
    http_status = 409
    error_code = ErrorCode.EXPENSE_NOT_EDITABLE

class RateLimitedError(DomainError):
    http_status = 429
    error_code = ErrorCode.RATE_LIMITED


errors_types = [
    AuthenticationError, ForbiddenError, NotFoundError, InternalError, BadRequest,
    DomainError, BoxFullError, BoxOutOfServiceError, PetAlreadyAssignedError,
    PetNotAssignedError, InsufficientStockError, DuplicateTaskInstanceError,
    InvalidRecurrenceRuleError, CannotDeleteWithActiveOccupancyError,
    CannotDeleteWithHistoryError, InvalidAuthorizationScopeError,
    MembershipNotActiveError, RoleNotAssignableError, RoleScopeMismatchError,
    PermissionEscalationNotAllowedError, LastAdminCannotBeRemovedError,
    DonationExceedsPetLimitError, ShelterNotVerifiedError, ShelterDonationsDisabledError,
    PetNotPublishedError, StripeChargesNotEnabledError, StripeTestModeViolationError,
    InvalidDonationAmountError, FundingNeedClosedError, ExpenseNotEditableError,
    RateLimitedError,
]

error_pagination = {
    "page": 0,
    "page_size": 0,
    "total_item": 0,
    "total_pages": 0
}

def format_error (e, token="Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjp7ImlkIjoiZWViMDJmMjctYTZkYi00ZDM5LWI0MWEtYzc3OTU2MDc4ZmIzIiwiZmlyc3RfbmFtZSI6IkFub25pbW8iLCJsYXN0X25hbWUiOiJBbm9uaW1vIiwiZW1haWwiOiJhbm9uQGFub24uY29tIiwicm9sZSI6IlVTRVIiLCJjcmVhdGVkX2F0IjoiMjAyMi0wNS0wNSAwMDowMDowMCJ9LCJpYXQiOjk5NTMzODQ0MzksImV4cCI6MTY1Mzk4OTIzOX0.0BsuDTn18kJo_bwpGNSvxo9W3L1szyGmHmvr77Pv-2o"): 
    if not isinstance(e, tuple(errors_types)) :
        logger.critical(
            "Exception not handled properly\n"\
            f"{type(e)}\n"\
            f"{e}"
        )
        try :
            user= get_request_user(token)
        except : 
            user = {
                "email":"anon@anon.anon",
                "first_name": "Anon",
                "last_name": "Anon"
            } 
        logger.warning('sending error to admin via TELEGRAM')
        send_message_to_admin(f"Poject: {cfg['project']['name']}\nutente: {user['email']} {user['first_name']} {user['last_name']}\ngenerated the following untracked error:\n\n🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫\n\n{str(e)}\n\n🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫 🚫")
        e= InternalError('Internal server error')
    ext = getattr(e, "extension", {}) or {}
    return {
        "message": str(e),
        "code": ext.get("code"),
        "error_code": ext.get("error_code", ErrorCode.INTERNAL),
        "extra": ext.get("extra"),
    }