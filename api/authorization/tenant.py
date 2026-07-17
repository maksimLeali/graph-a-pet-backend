"""Tenant scoping for legacy `commonSearch` list resolvers.

Historically these resolvers were only authenticated: any logged-in user could
list every shelter's rows by omitting/forging filters. This module closes the
gap without changing the GraphQL contract:

- callers holding the platform permission (default `platform.shelters.read`,
  PLATFORM_ADMIN via grants_all) keep the global, cross-tenant behaviour the
  back office relies on;
- every other caller MUST scope the search to exactly one shelter — directly
  (`shelter_id` filter) or through an entity the shelter can be derived from
  (`map_id`, `shelter_pet_id`, ...) — and hold the required shelter
  permission there. The shelter id is then trusted from the *verified*
  filter/entity, never from unvalidated client input.
"""
from api.errors import AuthenticationError, ForbiddenError
from domain.authorization import authorization_service
from domain.authorization.catalog import PlatformPermissions
from utils import get_request_user


def _filter_values(common_search, key):
    """All values for `key` across fixed and lists filters of a raw
    (pre-format_common_search) commonSearch dict."""
    filters = (common_search or {}).get("filters") or {}
    values = []
    for f in filters.get("fixed") or []:
        if f and f.get("key") == key and f.get("value") not in (None, ""):
            values.append(f["value"])
    for f in filters.get("lists") or []:
        if f and f.get("key") == key:
            values.extend(v for v in (f.get("value") or []) if v not in (None, ""))
    return values


# entity-filter key -> shelter_id resolver. Late imports: repositories touch
# the flask app at import time.

def _shelter_from_map(map_id):
    import repository.shelter_maps as maps_data
    m = maps_data.get_shelter_map(map_id)
    return m.get("shelter_id") if m else None


def _shelter_from_shelter_pet(shelter_pet_id):
    import repository.shelter_pets as shelter_pets_data
    sp = shelter_pets_data.get_shelter_pet(shelter_pet_id)
    return sp.get("shelter_id") if sp else None


MAP_SCOPE = {"map_id": _shelter_from_map}
SHELTER_PET_SCOPE = {"shelter_pet_id": _shelter_from_shelter_pet}


def require_tenant_common_search(
    info,
    common_search,
    permission,
    platform_permission=PlatformPermissions.SHELTERS_READ,
    alt_scopes=None,
):
    """Authorize a commonSearch list resolver. Returns the user dict.

    `alt_scopes`: {filter_key: fn(value) -> shelter_id} accepted when no
    direct shelter_id filter is present (e.g. MAP_SCOPE, SHELTER_PET_SCOPE).

    Raises ForbiddenError when the caller has no platform grant and the search
    is not scoped to exactly one shelter it holds `permission` on.
    """
    token = info.context.headers.get("authorization")
    try:
        user = get_request_user(token)
    except Exception:
        raise AuthenticationError("unauthorized")

    if authorization_service.can(user["id"], platform_permission):
        return user

    shelter_ids = set(_filter_values(common_search, "shelter_id"))
    if not shelter_ids:
        for key, resolve in (alt_scopes or {}).items():
            values = set(_filter_values(common_search, key))
            if len(values) > 1:
                raise ForbiddenError("cross-tenant search is not allowed")
            if values:
                shelter_id = resolve(next(iter(values)))
                if not shelter_id:
                    raise ForbiddenError(f"unknown {key} for tenant scoping")
                shelter_ids = {shelter_id}
                break

    if len(shelter_ids) != 1:
        raise ForbiddenError("this search must be scoped to a single shelter")

    authorization_service.authorize(
        user_id=user["id"],
        permission=permission,
        shelter_id=next(iter(shelter_ids)),
    )
    return user
