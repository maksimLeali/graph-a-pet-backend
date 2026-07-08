# Shelter System Overview

## What is a Shelter?

A shelter is a place that holds pets. Users with roles can manage pets, tasks, walks, boxes, and inventory inside a shelter.

---

## Data Models

| Model                 | What it is                                             |
| --------------------- | ------------------------------------------------------ |
| `Shelter`             | Name, address, contacts                                |
| `ShelterRole`         | Links a user to a shelter with a role                  |
| `ShelterPet`          | Links a pet to a shelter                               |
| `ShelterMap`          | Visual layout canvas (width, height, background image) |
| `ShelterArea`         | A section on the map                                   |
| `ShelterBox`          | A housing unit (cage, kennel, etc.) inside an area     |
| `ShelterBoxOccupancy` | Which pet is in which box, and when                    |
| `ShelterTask`         | A job to do (cleaning, feeding, meds, etc.)            |
| `ShelterWalk`         | An exercise session for a pet                          |
| `ShelterInventory`    | Stock items (food, medicine, supplies)                 |

---

## Roles & Permissions

| Role        | Can do                                                                   |
| ----------- | ------------------------------------------------------------------------ |
| `VOLUNTEER` | Read only                                                                |
| `STAFF`     | Complete tasks, record walks, check pets in/out, log inventory movements |
| `MANAGER`   | Create tasks, boxes, modify inventory                                    |
| `OWNER`     | Edit shelter info, manage roles                                          |
| `ADMIN`     | System-level actions (delete shelter)                                    |

---

## Key Workflows

### Add a Pet to a Shelter

1. Create a pet (name, birthday, gender, photo).
2. Link the pet to the shelter via `createShelterPet`.

### Assign a Pet to a Box

1. Pick a box (must not be full or out-of-service).
2. Call `assignPetToBox`. Records who moved the pet, when, and why.
3. To move: `movePetBetweenBoxes`. To release: `releasePetFromBox`.

### Tasks (Recurring)

1. A manager creates a task with a recurrence rule (daily, weekly, etc.).
2. Every night at 2am, a cron job creates today's pending instance automatically.
3. Staff mark tasks as `COMPLETED` or `SKIPPED`.

### Walks

1. Plan a walk (`PLANNED` status).
2. Staff starts it → status becomes `IN_PROGRESS`.
3. Staff finishes it → status becomes `COMPLETED`. Duration is auto-calculated.
4. Query `getPetsNeedingWalk` finds pets not walked in the last N hours.

### Inventory

- Each item has a minimum threshold.
- Movements: `RESTOCK`, `DONATION` (add stock), `CONSUMPTION`, `WASTE` (remove stock).
- Current quantity = sum of all movements.
- Low stock alert when quantity drops below threshold.

---

## GraphQL API (summary)

### Queries

- `listShelters` — paginated list
- `getShelter(id)` — single shelter with roles and pets
- `getShelterOperationalDashboard(shelter_id)` — metrics: walk status, task status, box usage, low stock
- `listShelterTasks`, `listShelterWalks`, `listShelterInventoryItems`, `listLowStockItems`
- `getPetsNeedingWalk(shelter_id, hours)`

### Mutations

- `createShelter`, `updateShelter`, `deleteShelter`
- `createShelterRole`, `updateShelterRole`, `deleteShelterRole`
- `createShelterPet`, `deleteShelterPet`, `changeShelter` (transfer pet to another shelter)
- `createShelterBox`, `updateShelterBox`, `markBoxCleaned`, `setBoxOutOfService`, `deleteShelterBox`
- `assignPetToBox`, `releasePetFromBox`, `movePetBetweenBoxes`
- `createShelterTask`, `completeShelterTask`, `skipShelterTask`, `deleteShelterTask`
- `createShelterWalk`, `startShelterWalk`, `completeShelterWalk`, `cancelShelterWalk`
- `createShelterInventoryItem`, `createShelterInventoryMovement`, `deleteShelterInventoryItem`

---

## Frontend Pages

| Page               | What it does                                        |
| ------------------ | --------------------------------------------------- |
| `Shelters`         | Lists all shelters as cards                         |
| `ShelterDetail`    | Main dashboard: info, roles, pets, metrics, tabs    |
| `AddShelterPet`    | Form to create a pet and link to shelter            |
| `ShelterTasksList` | View, complete, skip, delete tasks                  |
| `AddShelterTask`   | Form to create a task with recurrence config        |
| `ShelterWalksList` | See pets needing walks, plan and record walks       |
| `ShelterInventory` | View stock, add movements, delete items             |
| `AddInventoryItem` | Form to add a new stock item                        |
| `ShelterMapEditor` | Visual drag-drop editor for zones, areas, and boxes |
| `ShelterPetDetail` | Pet profile, current box, health info, move option  |

---

## File Locations

| What                            | Path                                    |
| ------------------------------- | --------------------------------------- |
| Backend shelter API             | `graph-a-pet-backend/api/shelters/`     |
| Backend shelter domain          | `graph-a-pet-backend/domain/shelters/`  |
| Backend shelter-related modules | `graph-a-pet-backend/api/shelter_*/`    |
| GraphQL schema                  | `graph-a-pet-backend/schema.graphql`    |
| Frontend shelter pages          | `graph-a-pet-app/src/modules/shelters/` |
| Cron jobs                       | `graph-a-pet-backend/utils/cron/`       |
