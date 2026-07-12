# RBAC migration inventory

Legacy authorization checks found in the repository, with their target
permission keys. Status legend: **MIGRATED** (pilot done), **SHADOWED**
(legacy still enforces, RBAC compared in shadow mode), **PENDING**.

Legacy systems:

- `api/middlewares.py` — `min_role(USER|ADMIN)`, `min_shelter_role(role)`, `assert_shelter_role(token, shelter_id, role)`; hierarchy `VOLUNTEER(1) < STAFF(2) < MANAGER(3) < OWNER(4)`; global `ADMIN` always bypasses.
- `api/permissions.py` — capability layer (`Cap.*`, `assert_capability`) mapped onto the same min-role hierarchy.

## Shelter Tasks (pilot — MIGRATED)

| File | Resolver | Legacy check | Permission | Scope | Status |
|---|---|---|---|---|---|
| api/shelter_tasks/mutations.py | createShelterTask | `min_shelter_role("STAFF")` | `shelters.tasks.create` | shelter | MIGRATED |
| api/shelter_tasks/mutations.py | updateShelterTask | `assert_shelter_role(STAFF)` | `shelters.tasks.update` | shelter | MIGRATED |
| api/shelter_tasks/mutations.py | completeShelterTask | `assert_shelter_role(STAFF)` | `shelters.tasks.execute` | shelter | MIGRATED |
| api/shelter_tasks/mutations.py | skipShelterTask | `assert_shelter_role(STAFF)` | `shelters.tasks.execute` | shelter | MIGRATED |
| api/shelter_tasks/mutations.py | deleteShelterTask | `assert_shelter_role(OWNER)` | `shelters.tasks.delete` | shelter | MIGRATED |
| api/shelter_tasks/queries.py | listOperationalShelterTasks | `assert_capability(Cap.READ)` | `shelters.tasks.read` | shelter | MIGRATED |
| api/shelter_tasks/queries.py | getShelterTask | `assert_capability(Cap.READ)` | `shelters.tasks.read` | shelter | MIGRATED |
| api/shelter_tasks/queries.py | listShelterTasks | `auth_middleware` only (no shelter check — pre-existing cross-tenant list, BO-style commonSearch) | — | — | PENDING (risk: needs platform perm or forced shelter filter) |

## Shelter Walks (SHADOWED)

| File | Operation | Legacy | Permission target |
|---|---|---|---|
| api/shelter_walks/mutations.py | create/start/complete/rate | STAFF | `shelters.walks.create` / `shelters.walks.execute` |
| api/shelter_walks/mutations.py | cancel | STAFF | `shelters.walks.cancel` |
| api/shelter_walks/mutations.py | delete | OWNER | `shelters.walks.delete` |
| api/shelter_walks/queries.py | operational list | Cap.READ / STAFF | `shelters.walks.read` |

## Inventory (SHADOWED)

| File | Operation | Legacy | Permission target |
|---|---|---|---|
| api/shelter_inventory/queries.py | list | STAFF | `shelters.inventory.read` |
| api/shelter_inventory/mutations.py | create/update item | MANAGER | `shelters.inventory.manage` |
| api/shelter_inventory/mutations.py | delete item | OWNER | `shelters.inventory.manage` (delete → SHELTER_ADMIN) |
| api/shelter_inventory/mutations.py | movement | STAFF | `shelters.inventory.consume` |
| api/shelter_inventory/mutations.py | negative override | MANAGER | `shelters.inventory.adjust` |

## Boxes / occupancies / maps / areas / zones / elements (SHADOWED)

| Operation | Legacy | Permission target |
|---|---|---|
| box create/update, map create/update, area/zone/element create/update | MANAGER | `shelters.boxes.manage` / `shelters.map.update` |
| box delete, map delete, area/zone/element delete | OWNER | SHELTER_ADMIN via `shelters.boxes.manage` / `shelters.map.update` |
| occupancy assign/move/release | STAFF | `shelters.boxes.assign_pet` / `shelters.boxes.release_pet` |
| box/occupancy reads | STAFF | `shelters.boxes.read` |

## People (SHADOWED)

| Operation | Legacy | Permission target |
|---|---|---|
| list/get people | STAFF | `shelters.people.read` |
| create person | STAFF | `shelters.people.create` |
| update person | MANAGER | `shelters.people.update` |
| archive person | MANAGER | `shelters.people.archive` |
| delete person | OWNER | SHELTER_ADMIN |

## Members / invites / roles (SHADOWED — highest risk)

| Operation | Legacy | Permission target | Notes |
|---|---|---|---|
| createShelterInvite | MANAGER | `shelters.members.invite` | |
| createShelterRole | **auth only — NO role check** | `shelters.roles.assign` | **security gap**: any authenticated user can self-assign OWNER today; RBAC migration closes it |
| updateShelterRole | **auth only — NO role check** | `shelters.roles.manage` | same gap |
| deleteShelterRole | global ADMIN | `shelters.roles.manage` or `platform.roles.manage` | |

## Ownership transfers / claim (SHADOWED)

| Operation | Legacy | Permission target |
|---|---|---|
| request transfer / list transfers | OWNER | `shelters.ownership.transfer` |
| claim create | auth | `shelters.claim.create` |
| claim review (approve/reject) | global ADMIN | `platform.claims.review` |
| listShelterClaimRequests | OWNER | `shelters.read` + domain rule |

## Global ADMIN (`min_role(ADMIN)`) resolvers (PENDING → platform.*)

users (list/get/update/delete), statistics (all), medias admin list, health_cards
admin queries, walks/walk_ratings admin, cures/pets/ownerships admin ops,
damnationes_memoriae, codes, shelters delete, shelter_pets delete,
claim review. Target: `platform.users.*`, `platform.shelters.*`,
`platform.claims.review`, `platform.audit.read`. Until migrated they stay on
`min_role(ADMIN)`; the backfill grants every legacy ADMIN the PLATFORM_ADMIN
role so the flip is a rename, not a behaviour change.

`min_role(USER)` resolvers (health_cards mutations, reports, users update-self)
map to `platform.app.use`, held by PLATFORM_USER which the backfill assigns to
every registered user. The back-office login gate maps to
`platform.backoffice.access` (covered by PLATFORM_ADMIN grants_all).

## Hard-coded ADMIN bypasses (to be funnelled through AuthorizationService)

| File:line | Bypass |
|---|---|
| api/permissions.py `has_capability` | ADMIN always true (kept during shadow) |
| api/middlewares.py `assert_shelter_role` | ADMIN always true (kept during shadow) |
| api/shelter_dashboard/queries.py:39 | `is_global_admin=` flag |
| domain/shelters/__init__.py:30 | PUBLIC visibility admin override |

## Frontend (app) legacy checks

| File | Check |
|---|---|
| src/modules/shelters/hooks/useMyShelterRole.ts | role fetch + `isAdmin` → replaced by `useShelterAuthorization` (tasks pilot) |
| ShelterDetail.tsx:116-120 | `canManage`/`isOwner` from role names — PENDING |
| ShelterInvites.tsx:22, ShelterPublicProfile.tsx:22, ShelterPeople.tsx:49 | `canManage = OWNER\|\|MANAGER` — PENDING |
| MainMenu.tsx:118, MyShelterDashboard.tsx:41, ShelterMapEditor.tsx:212 | `user.role === Admin` — PENDING |

## Back office legacy checks

| File | Check |
|---|---|
| src/components/shelters/MembersTab.tsx | role-name logic — PENDING |

## Ownership caveat

Legacy OWNER rows in `shelter_roles` are the only technical-ownership source
(claim approval, ownership transfer and workspace creation write them
directly). The backfill maps OWNER → SHELTER_ADMIN for capabilities but does
NOT delete or alter the legacy rows: they remain the domain ownership source
until a dedicated `shelter.owner_user_id`-style migration. Do not treat
holding SHELTER_ADMIN as proof of ownership.
