# RBAC permission matrix

Backend operation ↔ frontend action ↔ back-office action ↔ permission ↔ legacy roles.

System roles are **cumulative**, mirroring the real legacy hierarchy
(`VOLUNTEER < STAFF < MANAGER < OWNER`, verified in `api/permissions.py`
`ROLE_LEVEL` and every `assert_shelter_role` call site): each tier includes the
previous tier's grants. `V`=SHELTER_VOLUNTEER, `S`=SHELTER_STAFF,
`M`=SHELTER_MANAGER, `A`=SHELTER_ADMIN, `PA`=PLATFORM_ADMIN (grants-all).

## Shelter tasks (pilot — enforced by RBAC)

| Backend operation | App action | BO action | Permission | Min role |
|---|---|---|---|---|
| listOperationalShelterTasks / getShelterTask | tasks list/detail | Task tab list | `shelters.tasks.read` | V |
| completeShelterTask / skipShelterTask | complete/skip CTA | complete/skip | `shelters.tasks.execute` | V* |
| createShelterTask | new task page | create form | `shelters.tasks.create` | S |
| updateShelterTask | edit task | edit | `shelters.tasks.update` | S |
| deleteShelterTask | delete CTA | delete | `shelters.tasks.delete` | A |

\* divergence from legacy: complete/skip required STAFF; the spec target grants
execution to volunteers. Shadow mode logs `LEGACY_DENIED_RBAC_ALLOWED` for
volunteers executing tasks — accepted, it is the desired end state.

## Shelter walks

| Backend operation | Permission | Min role |
|---|---|---|
| list/get walks | `shelters.walks.read` | V |
| start/complete/rate walk | `shelters.walks.execute` | V* |
| create walk | `shelters.walks.create` | S |
| cancel walk | `shelters.walks.cancel` | S (legacy STAFF, spec said MANAGER — legacy wins) |
| delete walk | `shelters.walks.delete` | A (legacy OWNER, spec said MANAGER — legacy wins) |

## Inventory

| Backend operation | Permission | Min role |
|---|---|---|
| list items/movements | `shelters.inventory.read` | S (legacy denies VOLUNTEER) |
| consumption movement | `shelters.inventory.consume` | S |
| restock movement | `shelters.inventory.restock` | M |
| adjustment / negative override | `shelters.inventory.adjust` | M |
| item create/update/archive | `shelters.inventory.manage` | M |

## Boxes / map

| Backend operation | Permission | Min role |
|---|---|---|
| list boxes/occupancies | `shelters.boxes.read` | V |
| assign pet to box | `shelters.boxes.assign_pet` | S |
| release/move pet | `shelters.boxes.release_pet` | S |
| box create/update/delete | `shelters.boxes.manage` | M |
| map/areas/zones/elements read | `shelters.map.read` | V |
| map/areas/zones/elements write | `shelters.map.update` | M |

## Donations / funding needs / expenses

No backend entity yet (Donation, FundingNeed, Expense, FinancialReport are not
implemented) — this section defines the permission keys and role grants ahead
of the feature build, per `graph-a-pet-app/graph_a_pet_app_backend_summary.md`
Donations spec. `SHELTER_VOLUNTEER` gets none of these (donor amounts, donor
identity and financial reports must stay invisible to volunteers); volunteers
see funding needs only through the same public interface external users use.

| Backend operation (future) | Permission | Min role |
|---|---|---|
| view active funding needs (operational) | `shelters.funding_needs.read` | S |
| create/update/close funding need | `shelters.funding_needs.create` / `.update` / `.close` | M |
| view donation aggregates | `shelters.donations.read` | M |
| view donor identity / transaction details | `shelters.donations.read_details` | A (operationally required only) |
| configure default/override pet funding limit | `shelters.funding_limits.manage` / `.override` | A |
| view funding limits | `shelters.funding_limits.read` | M |
| register/update/submit expense | `shelters.expenses.create` / `.update` / `.submit` | M |
| approve/reject expense | `shelters.expenses.approve` | A |
| view expenses | `shelters.expenses.read` | M |
| activate/suspend shelter donations | `shelters.donations.enable` / `.disable` | A |
| manage public donation settings | `shelters.donations.settings.manage` | A |
| view/export financial reports | `shelters.financial_reports.read` / `.export` | A |
| publish shelter pets | `shelters.pets.publish` | M |
| manage public shelter profile | `shelters.public_profile.manage` | M |

Limit overrides (`shelters.funding_limits.override`) must always write an
audit record with `reason`, `effective period`, `actor`, `timestamp`.

## People / members / roles

| Backend operation | Permission | Min role |
|---|---|---|
| list/get people | `shelters.people.read` | S |
| create person | `shelters.people.create` | S (legacy STAFF, spec said MANAGER — legacy wins) |
| update person | `shelters.people.update` | M |
| archive person | `shelters.people.archive` | M |
| members list | `shelters.members.read` | M |
| create invite | `shelters.members.invite` | M |
| remove member | `shelters.members.remove` | A |
| roles read | `shelters.roles.read` | A |
| assign role | `shelters.roles.assign` | A |
| manage roles | `shelters.roles.manage` | A |

## Shelter admin / ownership

| Backend operation | Permission | Min role |
|---|---|---|
| update shelter info | `shelters.update` | A |
| request ownership transfer | `shelters.ownership.transfer` | A |
| create claim | `shelters.claim.create` | any authenticated (domain rules apply) |
| shelter pets read/update/remove | `shelters.pets.read` / `.update` / `.remove` | V / S / A |

## Platform

| Backend operation | Permission | Legacy |
|---|---|---|
| base app access (login-gated features) | `platform.app.use` | USER |
| back-office access gate | `platform.backoffice.access` | ADMIN |
| users admin | `platform.users.read` / `.update` | ADMIN |
| shelters admin/verify | `platform.shelters.read` / `.verify` | ADMIN |
| claim review | `platform.claims.review` | ADMIN |
| roles administration | `platform.roles.manage` | ADMIN |
| audit log read | `platform.audit.read` | ADMIN |

## Donor-side platform permissions (PLATFORM_USER)

No backend entity yet — see the Donations section above. Guest (unauthenticated)
donors stay outside RBAC entirely: enforced via public API rate limiting and
payment validation, never a role.

| Backend operation (future) | Permission |
|---|---|
| create a donation | `platform.donations.create` |
| view own donation history | `platform.donations.read_own` |
| request refund/transaction assistance | `platform.donations.request_refund` |
| view own saved payment methods (masked) | `platform.payment_methods.read_own` |
| save/manage own payment methods | `platform.payment_methods.manage_own` |

## Platform financial administration

`PLATFORM_ADMIN` gets these via `grants_all_permissions`. `PLATFORM_FINANCE_OPERATOR`
(optional/future role, no legacy tier) gets a subset — payment support without
user/role/shelter administration.

| Backend operation (future) | Permission | PLATFORM_FINANCE_OPERATOR |
|---|---|---|
| inspect all donations | `platform.donations.read` | yes |
| inspect donor/transaction details | `platform.donations.read_details` | yes |
| full/partial refund | `platform.donations.refund` / `.partial_refund` | yes |
| suspend shelter donations | `platform.donations.suspend` | no |
| view/handle disputes | `platform.disputes.read` / `.manage` | yes |
| view/manage connected accounts | `platform.connected_accounts.read` / `.manage` | read only |
| read/reconcile financial ledger | `platform.financial_ledger.read` / `.reconcile` | yes |
| read/retry webhooks | `platform.webhooks.read` / `.retry` | read only |

`PLATFORM_FINANCE_OPERATOR` must never receive `platform.users.*`,
`platform.roles.manage`, `platform.shelters.verify` or `platform.donations.suspend`.

## Legacy → RBAC role mapping (backfill)

| Legacy | RBAC role | Notes |
|---|---|---|
| shelter_roles.VOLUNTEER | SHELTER_VOLUNTEER | + membership ACTIVE |
| shelter_roles.STAFF | SHELTER_STAFF | + membership ACTIVE |
| shelter_roles.MANAGER | SHELTER_MANAGER | + membership ACTIVE |
| shelter_roles.OWNER | SHELTER_ADMIN | membership source WORKSPACE_CREATOR on personal workspaces; legacy row kept as ownership source |
| every users row | PLATFORM_USER | platform scope, `platform.app.use` (base app access) |
| users.role = ADMIN | PLATFORM_ADMIN | platform scope, grants_all (covers back office + `platform.backoffice.access`) — on top of PLATFORM_USER |

## Documented divergences (legacy behaviour kept over spec draft)

1. `tasks.create`, `tasks.update` at STAFF (spec draft: MANAGER) — legacy allowed STAFF.
2. `tasks.delete`, `walks.delete` at SHELTER_ADMIN (spec draft: MANAGER) — legacy required OWNER.
3. `walks.cancel`, `people.create` at STAFF (spec draft: MANAGER) — legacy allowed STAFF.
4. `inventory.read` at STAFF (spec draft: VOLUNTEER) — legacy denied volunteers.
5. SHELTER_ADMIN includes all SHELTER_MANAGER permissions — legacy OWNER ≥ MANAGER (cumulative hierarchy), so a single SHELTER_ADMIN role keeps parity; assigning admin+manager together is not required.
6. `tasks.execute` / `walks.execute` at VOLUNTEER (legacy: STAFF) — intentional spec adoption, see pilot note.
7. Donations/funding needs/expenses/financial reports have no legacy predecessor at all — no divergence to reconcile, catalog follows the spec draft directly.
