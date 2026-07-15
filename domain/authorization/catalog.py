"""Central RBAC permission catalog.

Single source of truth for every permission key persisted in the database.
Keys follow the `domain.resource.action` convention; the string is the stable
contract, the constants exist so application code cannot typo a key.

Role seed definitions live here too so the seed script, the backfill and the
tests all share one description of what each system role grants.
"""


class ShelterPermissions:
    READ = "shelters.read"
    UPDATE = "shelters.update"

    MEMBERS_READ = "shelters.members.read"
    MEMBERS_INVITE = "shelters.members.invite"
    MEMBERS_REMOVE = "shelters.members.remove"

    ROLES_READ = "shelters.roles.read"
    ROLES_ASSIGN = "shelters.roles.assign"
    ROLES_MANAGE = "shelters.roles.manage"

    PEOPLE_READ = "shelters.people.read"
    PEOPLE_CREATE = "shelters.people.create"
    PEOPLE_UPDATE = "shelters.people.update"
    PEOPLE_ARCHIVE = "shelters.people.archive"

    PETS_READ = "shelters.pets.read"
    PETS_CREATE = "shelters.pets.create"
    PETS_UPDATE = "shelters.pets.update"
    PETS_REMOVE = "shelters.pets.remove"
    PETS_MEDICAL_READ = "shelters.pets.medical.read"
    PETS_MEDICAL_UPDATE = "shelters.pets.medical.update"

    TASKS_READ = "shelters.tasks.read"
    TASKS_CREATE = "shelters.tasks.create"
    TASKS_UPDATE = "shelters.tasks.update"
    TASKS_EXECUTE = "shelters.tasks.execute"
    TASKS_DELETE = "shelters.tasks.delete"

    WALKS_READ = "shelters.walks.read"
    WALKS_CREATE = "shelters.walks.create"
    WALKS_EXECUTE = "shelters.walks.execute"
    WALKS_CANCEL = "shelters.walks.cancel"
    WALKS_DELETE = "shelters.walks.delete"

    INVENTORY_READ = "shelters.inventory.read"
    INVENTORY_CONSUME = "shelters.inventory.consume"
    INVENTORY_RESTOCK = "shelters.inventory.restock"
    INVENTORY_ADJUST = "shelters.inventory.adjust"
    INVENTORY_MANAGE = "shelters.inventory.manage"

    BOXES_READ = "shelters.boxes.read"
    BOXES_MANAGE = "shelters.boxes.manage"
    BOXES_ASSIGN_PET = "shelters.boxes.assign_pet"
    BOXES_RELEASE_PET = "shelters.boxes.release_pet"

    MAP_READ = "shelters.map.read"
    MAP_UPDATE = "shelters.map.update"

    OWNERSHIP_TRANSFER = "shelters.ownership.transfer"
    CLAIM_CREATE = "shelters.claim.create"

    PETS_PUBLISH = "shelters.pets.publish"

    DONATIONS_READ = "shelters.donations.read"
    DONATIONS_READ_DETAILS = "shelters.donations.read_details"
    DONATIONS_SETTINGS_MANAGE = "shelters.donations.settings.manage"
    DONATIONS_ENABLE = "shelters.donations.enable"
    DONATIONS_DISABLE = "shelters.donations.disable"

    FUNDING_NEEDS_READ = "shelters.funding_needs.read"
    FUNDING_NEEDS_CREATE = "shelters.funding_needs.create"
    FUNDING_NEEDS_UPDATE = "shelters.funding_needs.update"
    FUNDING_NEEDS_CLOSE = "shelters.funding_needs.close"

    FUNDING_LIMITS_READ = "shelters.funding_limits.read"
    FUNDING_LIMITS_MANAGE = "shelters.funding_limits.manage"
    FUNDING_LIMITS_OVERRIDE = "shelters.funding_limits.override"

    EXPENSES_READ = "shelters.expenses.read"
    EXPENSES_CREATE = "shelters.expenses.create"
    EXPENSES_UPDATE = "shelters.expenses.update"
    EXPENSES_SUBMIT = "shelters.expenses.submit"
    EXPENSES_APPROVE = "shelters.expenses.approve"

    FINANCIAL_REPORTS_READ = "shelters.financial_reports.read"
    FINANCIAL_REPORTS_EXPORT = "shelters.financial_reports.export"

    PUBLIC_PROFILE_MANAGE = "shelters.public_profile.manage"


class PlatformPermissions:
    # base application access, granted to every registered user
    APP_USE = "platform.app.use"
    # back-office access gate; PLATFORM_ADMIN covers it via grants_all
    BACKOFFICE_ACCESS = "platform.backoffice.access"

    USERS_READ = "platform.users.read"
    USERS_UPDATE = "platform.users.update"
    SHELTERS_READ = "platform.shelters.read"
    SHELTERS_VERIFY = "platform.shelters.verify"
    CLAIMS_REVIEW = "platform.claims.review"
    ROLES_MANAGE = "platform.roles.manage"
    AUDIT_READ = "platform.audit.read"

    # donor-side (guest donor stays outside RBAC; these apply to
    # PLATFORM_USER, the standard authenticated donor)
    DONATIONS_CREATE = "platform.donations.create"
    DONATIONS_READ_OWN = "platform.donations.read_own"
    DONATIONS_REQUEST_REFUND = "platform.donations.request_refund"
    PAYMENT_METHODS_READ_OWN = "platform.payment_methods.read_own"
    PAYMENT_METHODS_MANAGE_OWN = "platform.payment_methods.manage_own"

    # platform financial administration
    DONATIONS_READ = "platform.donations.read"
    DONATIONS_READ_DETAILS = "platform.donations.read_details"
    DONATIONS_REFUND = "platform.donations.refund"
    DONATIONS_PARTIAL_REFUND = "platform.donations.partial_refund"
    DONATIONS_SUSPEND = "platform.donations.suspend"
    DISPUTES_READ = "platform.disputes.read"
    DISPUTES_MANAGE = "platform.disputes.manage"
    CONNECTED_ACCOUNTS_READ = "platform.connected_accounts.read"
    CONNECTED_ACCOUNTS_MANAGE = "platform.connected_accounts.manage"
    FINANCIAL_LEDGER_READ = "platform.financial_ledger.read"
    FINANCIAL_LEDGER_RECONCILE = "platform.financial_ledger.reconcile"
    WEBHOOKS_READ = "platform.webhooks.read"
    WEBHOOKS_RETRY = "platform.webhooks.retry"


SCOPE_SHELTER = "SHELTER"
SCOPE_PLATFORM = "PLATFORM"


def _perms(cls):
    return [v for k, v in vars(cls).items() if not k.startswith("_") and isinstance(v, str)]


# key -> (domain, action, scope_type, risk_level, description)
def _meta(key, risk="LOW", description=""):
    parts = key.split(".")
    scope = SCOPE_PLATFORM if parts[0] == "platform" else SCOPE_SHELTER
    return {
        "key": key,
        "domain": parts[0],
        "action": ".".join(parts[1:]),
        "scope_type": scope,
        "risk_level": risk,
        "description": description,
    }


HIGH_RISK = {
    ShelterPermissions.ROLES_ASSIGN,
    ShelterPermissions.ROLES_MANAGE,
    ShelterPermissions.MEMBERS_REMOVE,
    ShelterPermissions.OWNERSHIP_TRANSFER,
    PlatformPermissions.USERS_UPDATE,
    PlatformPermissions.SHELTERS_VERIFY,
    PlatformPermissions.CLAIMS_REVIEW,
    PlatformPermissions.ROLES_MANAGE,

    ShelterPermissions.DONATIONS_ENABLE,
    ShelterPermissions.DONATIONS_DISABLE,
    ShelterPermissions.FUNDING_LIMITS_OVERRIDE,
    ShelterPermissions.EXPENSES_APPROVE,
    PlatformPermissions.DONATIONS_REFUND,
    PlatformPermissions.DONATIONS_PARTIAL_REFUND,
    PlatformPermissions.DONATIONS_SUSPEND,
    PlatformPermissions.DISPUTES_MANAGE,
    PlatformPermissions.CONNECTED_ACCOUNTS_MANAGE,
    PlatformPermissions.FINANCIAL_LEDGER_RECONCILE,
}

MEDIUM_RISK = {
    PlatformPermissions.BACKOFFICE_ACCESS,
    ShelterPermissions.UPDATE,
    ShelterPermissions.MEMBERS_INVITE,
    ShelterPermissions.TASKS_DELETE,
    ShelterPermissions.WALKS_DELETE,
    ShelterPermissions.PETS_REMOVE,
    ShelterPermissions.PEOPLE_ARCHIVE,
    ShelterPermissions.INVENTORY_MANAGE,
    ShelterPermissions.INVENTORY_ADJUST,
    ShelterPermissions.BOXES_MANAGE,
    ShelterPermissions.MAP_UPDATE,
    PlatformPermissions.AUDIT_READ,

    ShelterPermissions.DONATIONS_READ_DETAILS,
    ShelterPermissions.DONATIONS_SETTINGS_MANAGE,
    ShelterPermissions.FUNDING_LIMITS_MANAGE,
    ShelterPermissions.FINANCIAL_REPORTS_READ,
    ShelterPermissions.FINANCIAL_REPORTS_EXPORT,
    ShelterPermissions.EXPENSES_SUBMIT,
    PlatformPermissions.DONATIONS_READ_DETAILS,
    PlatformPermissions.DISPUTES_READ,
    PlatformPermissions.CONNECTED_ACCOUNTS_READ,
    PlatformPermissions.FINANCIAL_LEDGER_READ,
    PlatformPermissions.WEBHOOKS_RETRY,
}


def _risk(key):
    if key in HIGH_RISK:
        return "HIGH"
    if key in MEDIUM_RISK:
        return "MEDIUM"
    return "LOW"


ALL_PERMISSION_KEYS = _perms(ShelterPermissions) + _perms(PlatformPermissions)

PERMISSION_CATALOG = [_meta(k, _risk(k)) for k in ALL_PERMISSION_KEYS]

_VALID_KEYS = set(ALL_PERMISSION_KEYS)


def is_valid_permission(key):
    return key in _VALID_KEYS


def assert_valid_permission(key):
    """Guard against typos: every permission string used by application code
    must exist in this catalog."""
    if key not in _VALID_KEYS:
        raise ValueError(f"unknown permission key: {key}")
    return key


# ---------------------------------------------------------------------------
# System role seeds.
#
# Grants mirror the *actual legacy behaviour* (cumulative hierarchy
# VOLUNTEER < STAFF < MANAGER < OWNER found in api/permissions.py and the
# assert_shelter_role call sites), not the role names. Divergences from the
# spec draft are documented in docs/rbac-permission-matrix.md.
# ---------------------------------------------------------------------------

P = ShelterPermissions

SHELTER_VOLUNTEER_PERMISSIONS = [
    P.READ,
    P.PETS_READ,
    P.TASKS_READ,
    P.TASKS_EXECUTE,   # legacy: complete/skip required STAFF, but execute-only
                       # volunteers are the spec target; kept as spec since
                       # legacy VOLUNTEER could not write anything — see matrix
    P.WALKS_READ,
    P.WALKS_EXECUTE,
    P.BOXES_READ,
    P.MAP_READ,
]

SHELTER_STAFF_PERMISSIONS = SHELTER_VOLUNTEER_PERMISSIONS + [
    P.PETS_UPDATE,
    P.PEOPLE_READ,
    P.PEOPLE_CREATE,       # legacy: createShelterPerson required STAFF
    P.TASKS_CREATE,        # legacy: createShelterTask required STAFF
    P.TASKS_UPDATE,        # legacy: updateShelterTask required STAFF
    P.WALKS_CREATE,
    P.WALKS_CANCEL,        # legacy: cancel walk required STAFF
    P.INVENTORY_READ,      # legacy: inventory list required STAFF
    P.INVENTORY_CONSUME,
    P.BOXES_ASSIGN_PET,
    P.BOXES_RELEASE_PET,
    P.FUNDING_NEEDS_READ,  # operational visibility only — no donor/financial data
]

SHELTER_MANAGER_PERMISSIONS = SHELTER_STAFF_PERMISSIONS + [
    P.PEOPLE_UPDATE,
    P.PEOPLE_ARCHIVE,
    P.INVENTORY_RESTOCK,
    P.INVENTORY_ADJUST,
    P.INVENTORY_MANAGE,
    P.BOXES_MANAGE,
    P.MAP_UPDATE,
    P.MEMBERS_READ,
    P.MEMBERS_INVITE,

    P.DONATIONS_READ,
    P.FUNDING_NEEDS_CREATE,
    P.FUNDING_NEEDS_UPDATE,
    P.FUNDING_NEEDS_CLOSE,
    P.FUNDING_LIMITS_READ,
    P.EXPENSES_READ,
    P.EXPENSES_CREATE,
    P.EXPENSES_UPDATE,
    P.EXPENSES_SUBMIT,
    P.PUBLIC_PROFILE_MANAGE,
    P.PETS_PUBLISH,
]

SHELTER_ADMIN_PERMISSIONS = SHELTER_MANAGER_PERMISSIONS + [
    P.UPDATE,
    P.MEMBERS_REMOVE,
    P.ROLES_READ,
    P.ROLES_ASSIGN,
    P.ROLES_MANAGE,
    P.OWNERSHIP_TRANSFER,
    P.TASKS_DELETE,        # legacy: deleteShelterTask required OWNER
    P.WALKS_DELETE,        # legacy: deleteShelterWalk required OWNER
    P.PETS_REMOVE,

    P.DONATIONS_READ_DETAILS,
    P.DONATIONS_SETTINGS_MANAGE,
    P.DONATIONS_ENABLE,
    P.DONATIONS_DISABLE,
    P.FUNDING_LIMITS_MANAGE,
    P.FUNDING_LIMITS_OVERRIDE,
    P.EXPENSES_APPROVE,
    P.FINANCIAL_REPORTS_READ,
    P.FINANCIAL_REPORTS_EXPORT,
]

PLATFORM_USER_PERMISSIONS = [
    PlatformPermissions.APP_USE,
    PlatformPermissions.DONATIONS_CREATE,
    PlatformPermissions.DONATIONS_READ_OWN,
    PlatformPermissions.DONATIONS_REQUEST_REFUND,
    PlatformPermissions.PAYMENT_METHODS_READ_OWN,
    PlatformPermissions.PAYMENT_METHODS_MANAGE_OWN,
]

PLATFORM_FINANCE_OPERATOR_PERMISSIONS = [
    PlatformPermissions.BACKOFFICE_ACCESS,
    PlatformPermissions.DONATIONS_READ,
    PlatformPermissions.DONATIONS_READ_DETAILS,
    PlatformPermissions.DONATIONS_REFUND,
    PlatformPermissions.DONATIONS_PARTIAL_REFUND,
    PlatformPermissions.DISPUTES_READ,
    PlatformPermissions.DISPUTES_MANAGE,
    PlatformPermissions.CONNECTED_ACCOUNTS_READ,
    PlatformPermissions.FINANCIAL_LEDGER_READ,
    PlatformPermissions.FINANCIAL_LEDGER_RECONCILE,
    PlatformPermissions.WEBHOOKS_READ,
]

SYSTEM_ROLES = [
    {
        "code": "PLATFORM_USER",
        "name": "User",
        "description": "Base platform access: every registered user can use the app.",
        "scope_type": SCOPE_PLATFORM,
        "grants_all_permissions": False,
        "permissions": PLATFORM_USER_PERMISSIONS,
        "legacy_role": "USER",
    },
    {
        "code": "SHELTER_VOLUNTEER",
        "name": "Volunteer",
        "description": "Read access plus task/walk execution inside one shelter.",
        "scope_type": SCOPE_SHELTER,
        "grants_all_permissions": False,
        "permissions": SHELTER_VOLUNTEER_PERMISSIONS,
        "legacy_role": "VOLUNTEER",
    },
    {
        "code": "SHELTER_STAFF",
        "name": "Staff",
        "description": "Day-to-day shelter operations: tasks, walks, inventory movements, box check-in/out.",
        "scope_type": SCOPE_SHELTER,
        "grants_all_permissions": False,
        "permissions": SHELTER_STAFF_PERMISSIONS,
        "legacy_role": "STAFF",
    },
    {
        "code": "SHELTER_MANAGER",
        "name": "Manager",
        "description": "Shelter coordination: people, inventory items, boxes, maps, invites.",
        "scope_type": SCOPE_SHELTER,
        "grants_all_permissions": False,
        "permissions": SHELTER_MANAGER_PERMISSIONS,
        "legacy_role": "MANAGER",
    },
    {
        "code": "SHELTER_ADMIN",
        "name": "Shelter admin",
        "description": "Full shelter administration including roles, members and ownership transfer.",
        "scope_type": SCOPE_SHELTER,
        "grants_all_permissions": False,
        "permissions": SHELTER_ADMIN_PERMISSIONS,
        "legacy_role": "OWNER",
    },
    {
        "code": "PLATFORM_ADMIN",
        "name": "Platform admin",
        "description": "Platform-wide administration; grants every permission in every scope.",
        "scope_type": SCOPE_PLATFORM,
        "grants_all_permissions": True,
        "permissions": [],
        "legacy_role": "ADMIN",
    },
    {
        # optional/future role — not backed by any legacy tier; assign
        # explicitly to payment-support staff instead of PLATFORM_ADMIN so
        # they get financial operations without user/role/system administration.
        "code": "PLATFORM_FINANCE_OPERATOR",
        "name": "Finance operator",
        "description": "Back-office payment support: refunds, disputes, connected accounts, "
                        "ledger reconciliation and webhook retries — no user/role/shelter administration.",
        "scope_type": SCOPE_PLATFORM,
        "grants_all_permissions": False,
        "permissions": PLATFORM_FINANCE_OPERATOR_PERMISSIONS,
        "legacy_role": None,
    },
]

LEGACY_SHELTER_ROLE_TO_RBAC = {
    "VOLUNTEER": "SHELTER_VOLUNTEER",
    "STAFF": "SHELTER_STAFF",
    "MANAGER": "SHELTER_MANAGER",
    "OWNER": "SHELTER_ADMIN",
}

# users.role (global) -> platform RBAC role. Every user gets PLATFORM_USER;
# legacy ADMIN gets PLATFORM_ADMIN on top of it.
LEGACY_GLOBAL_ROLE_TO_RBAC = {
    "USER": "PLATFORM_USER",
    "ADMIN": "PLATFORM_ADMIN",
}
