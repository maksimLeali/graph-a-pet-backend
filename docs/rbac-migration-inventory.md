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
| api/shelter_tasks/queries.py | listShelterTasks | `auth_middleware` only (no shelter check — pre-existing cross-tenant list, BO-style commonSearch) | `shelters.tasks.read` scoped OR `platform.shelters.read` global | shelter/platform | **MIGRATED** (`require_tenant_common_search`) |

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
| createShelterRole | **auth only — NO role check** | `shelters.roles.assign` (+ `shelters.ownership.transfer` per assegnare OWNER) | **MIGRATED** — gap self-OWNER chiuso; i flussi di dominio (createShelter, invites, transfers, claims, join requests) scrivono direttamente e non passano da questo resolver |
| updateShelterRole | **auth only — NO role check** | `shelters.roles.manage` (+ `shelters.ownership.transfer` per promuovere a OWNER); shelter ricavato dall'entità | **MIGRATED** |
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
| src/components/shelters/MembersTab.tsx | role-name logic — **MIGRATED** (CTA gated su `canShelter`/`canPlatform`, conferme col nome rifugio) |
| Topbar `RoleBadge` (user.role da cookie) | **MIGRATED** — rimosso; ruolo del rifugio mostrato solo come info nello switcher |

## Ownership caveat

Legacy OWNER rows in `shelter_roles` are the only technical-ownership source
(claim approval, ownership transfer and workspace creation write them
directly). The backfill maps OWNER → SHELTER_ADMIN for capabilities but does
NOT delete or alter the legacy rows: they remain the domain ownership source
until a dedicated `shelter.owner_user_id`-style migration. Do not treat
holding SHELTER_ADMIN as proof of ownership.

## Multi-shelter back office (2026-07-17)

- New permission `shelters.backoffice.access` (MEDIUM): area-entry gate for the
  back office, granted to SHELTER_MANAGER (and SHELTER_ADMIN by inheritance),
  NOT to STAFF/VOLUNTEER. It never replaces functional permissions.
  **Run `flask seed-rbac` after deploy** to register the key and the grants.
- New query `backofficeAccessContext`: platform permissions + all-and-only
  accessible shelters (ACTIVE membership, active assignment, backoffice access)
  with per-shelter effective permissions. Resolver uses AuthorizationService;
  role codes returned are informational only.
- `require_tenant_common_search` (api/authorization/tenant.py) now guards the
  legacy cross-tenant `commonSearch` lists: tasks, roles, pets, walks
  (accepts `shelter_pet_id` scope), inventory items+movements, maps, boxes /
  areas / zones / map elements / box occupancies (accept `map_id` scope).
  Platform callers with `platform.shelters.read` keep the global behaviour
  (documented divergence from the "separate platformSearch* queries" spec: no
  GraphQL breaking change, the dual behaviour is explicit in the guard).
- Still PENDING: single-entity get-by-id resolvers that remain auth-only
  (getShelterBox/Area/Zone/Map/Pet/Role, …) — bulk exfiltration is closed,
  per-id reads still need entity→shelter authorization like getShelterTask.
- Back office frontend is now permission-based (BackofficeAuthProvider,
  canPlatform/canShelter); the mobile app legacy checks (useMyShelterRole,
  ShelterDetail, MainMenu, …) remain PENDING as tracked above.

## Platform-admin access mode on shelters (2026-07-17, follow-up)

- `BackofficeShelterAccess.access_mode`: `MEMBERSHIP` (assignment shelter-scoped
  attivi + membership ACTIVE) vs `PLATFORM_ADMIN` (accesso concesso dal solo
  privilegio platform, senza membership). `membership_status` è ora nullable
  (null in modalità PLATFORM_ADMIN). `platform_override_active` segnala quando
  i privilegi platform aggiungono permission oltre la membership (solo UI).
- Nuova query `backofficeShelterAccess(shelter_id)`: risolve on-demand
  l'accesso a un singolo rifugio (usata dal BO quando un platform admin apre
  un rifugio fuori dalla propria lista membership). Nessuna membership o ruolo
  viene creato implicitamente.
- `AuthorizationService` ora distingue il canale membership dal canale
  platform (`_effective_permissions(..., return_detail=True)` /
  `shelter_access_breakdown`). Le operazioni HIGH_RISK concesse dal solo
  canale platform su un rifugio vengono tracciate in audit come
  `PLATFORM_ADMIN_SENSITIVE_OPERATION` (actor, shelter, permission).
- BO: banner persistente nell'area rifugio in modalità PLATFORM_ADMIN, label
  switcher "Platform admin" / "<ruolo> + platform", `lastShelterId` salvato
  solo per accessi via membership, link "Apri back office rifugio" dal
  dettaglio platform.

## Cutover RBAC completo (2026-07-17)

Legacy authorization layer RIMOSSO:

- `api/permissions.py` (Cap.*, assert_capability, has_capability, ROLE_LEVEL,
  is_restricted_to_assigned) — eliminato; `api/middlewares.py` ridotto al solo
  `auth_middleware` (min_role / min_shelter_role / assert_shelter_role
  eliminati); `domain/authorization/shadow.py` eliminato (shadow mode chiuso).
- Tutti i resolver usano `require_permission` / `authorize_from_token`
  (AuthorizationService). `min_role(ADMIN)` → permission platform esplicite:
  `platform.users.{read,update,delete}`, `platform.shelters.manage`,
  `platform.statistics.read`, `platform.content.manage` (admin CRUD entità
  pet-domain), `platform.audit.read` (damnationes), `platform.claims.review`.
  `min_role(USER)` → `platform.app.use`.
- Nuove permission shelter: `shelters.people.delete`, `shelters.people.link_user`
  (legacy OWNER-only). Divergenze documentate: delete di inventory item /
  box / map / area / zone / element ora richiedono la permission `*.manage`
  (MANAGER+) invece di OWNER-only.
- Bypass ADMIN rimossi: dashboard `is_global_admin`, visibilità PUBLIC
  (`platform.shelters.verify`), invito pet ownership e restore damnatio
  (`platform.content.manage`). Nessun resolver/domain legge più `users.role`.

Ownership tecnica separata:

- Tabella `shelter_ownerships` (migration `4c512b45c3c4`), stati
  ACTIVE/TRANSFER_PENDING/ENDED/REVOKED, source WORKSPACE_CREATOR/
  CLAIM_APPROVAL/OWNERSHIP_TRANSFER/PLATFORM_ASSIGNMENT/MIGRATION; unique
  parziale su (shelter,user) ACTIVE.
- OwnershipService (`domain/shelter_ownerships`): is_active_owner,
  require_active_owner, add_owner, remove_owner (vincolo ultimo owner),
  transfer_ownership (transazionale). Audit su ogni modifica.
- Flussi agganciati: creazione personal workspace, approvazione claim
  (ownership al requester, chiusura ownership precedenti), accettazione
  transfer. `request_transfer` verifica `is_active_owner` (fallback legacy
  finché il backfill non è girato).

CLI:

- `flask seed-rbac` — da rieseguire (nuove permission).
- `flask backfill-rbac` — ora completo: PLATFORM_USER a tutti, PLATFORM_ADMIN
  ai legacy ADMIN, sync ruoli shelter, ShelterOwnership per ogni OWNER legacy
  (source MIGRATION); transazionale per shelter, idempotente, report contatori.
- `flask diagnose-rbac` — diagnostica read-only pre-cutover; exit non-zero sui
  blocker (shelter senza owner, assignment scope inconsistenti, ecc.).

GraphQL:

- `ShelterAuthorization` += `roles` (informativo) e `is_technical_owner`
  (deriva da ShelterOwnership); `BackofficeShelterAccess` += `is_technical_owner`.
- `User.role` marcato `@deprecated` (informativo, mai autorizzativo).

Frontend app (mobile) migrata alle permission:

- `useMyShelterRole` ELIMINATO; tutti i consumer usano `useShelterAuthorization`
  (`can("shelters.…")`): RequireShelterMember/ShelterPublic (`shelters.read`),
  WalksList (`walks.create`), PetDetail (`pets.update`), People
  (`people.update` + `members.remove`), Invites (`members.invite`),
  PublicProfile (`public_profile.manage`), MapEditor (`map.update` /
  `boxes.assign_pet`). MyShelterDashboard: sezione inventory guidata dai dati
  (il backend filtra per `shelters.inventory.read`). MainMenu: rimosso il gate
  `user.role === ADMIN` sul toggle griglia (preferenza UI, non sicurezza).

Residui (fase Contract, dopo verifica dati in produzione):

- Tabella `shelter_roles`: NESSUNA lettura autorizzativa; resta scritta dai
  flussi dominio (invites, join requests, claim, transfer, workspace) con
  dual-write RBAC (`sync_legacy_shelter_role`) e letta solo come dato
  informativo (chip ruolo, liste BO). Drop possibile solo dopo migrazione
  delle query GraphQL `shelterRoles`/`listShelterRoles` a user_roles.
- Colonna `users.role`: solo dato informativo nel JWT/me; campo GraphQL
  deprecato. Drop colonna dopo aggiornamento client.
- Eseguire in ordine: `seed-rbac` → `backfill-rbac` → `diagnose-rbac` (deve
  dare 0 blocker) prima di considerare il cutover dati completo.
