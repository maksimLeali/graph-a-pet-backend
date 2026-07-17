"""Flask CLI commands.

Run with `flask <command>` (FLASK_APP=app.py is already set in
docker-compose.yml). Registered on the shared `app` in api/__init__.py.
"""
import click


def register_cli(app):
    @app.cli.command("seed-rbac")
    def seed_rbac():
        """Idempotently upsert every permission and system role defined in
        domain.authorization.catalog (PERMISSION_CATALOG, SYSTEM_ROLES) into
        the database, syncing each role's permission set to exactly what the
        catalog defines.

        Safe to re-run any time the catalog changes: adding, removing or
        reassigning a permission key updates existing rows instead of
        duplicating them (see repository.authorization.upsert_permission /
        upsert_system_role / sync_role_permissions). This is the seed script
        referenced by domain/authorization/shadow.py and catalog.py that did
        not exist yet.
        """
        # late imports: keep module import cheap, avoid app-bootstrap cycles
        from repository import db
        from domain.authorization.catalog import PERMISSION_CATALOG, SYSTEM_ROLES
        from utils.logger import logger
        import repository.authorization as authz_data

        try:
            for meta in PERMISSION_CATALOG:
                authz_data.upsert_permission(meta)
            click.echo(f"permissions: upserted {len(PERMISSION_CATALOG)}")

            for definition in SYSTEM_ROLES:
                role = authz_data.upsert_system_role(definition)
                added, removed = authz_data.sync_role_permissions(
                    role["id"], definition["permissions"]
                )
                click.echo(
                    f"role {definition['code']}: +{added} permission(s), "
                    f"-{removed} stale permission(s)"
                )

            db.session.commit()
            click.echo("rbac seed complete")
        except Exception as e:
            db.session.rollback()
            logger.error(f"rbac seed failed: {e}")
            raise click.ClickException(str(e))

    @app.cli.command("backfill-rbac")
    def backfill_rbac():
        """Full legacy -> RBAC backfill (idempotent, re-runnable; run
        seed-rbac first):

          * every legacy ShelterRole row -> membership + shelter assignment
            (VOLUNTEER/STAFF/MANAGER -> SHELTER_*, OWNER -> SHELTER_ADMIN);
          * every legacy OWNER row -> ShelterOwnership ACTIVE (source
            MIGRATION), technical ownership separated from SHELTER_ADMIN;
          * every user -> PLATFORM_USER; every users.role = ADMIN ->
            PLATFORM_ADMIN on top.

        Per-shelter work is transactional; already-migrated data is skipped.
        Prints a full counter report and never deletes legacy rows."""
        from repository import db
        from repository.shelter_roles.models import ShelterRole, RoleLevel
        from repository.users.models import User, UserRole
        import repository.authorization as authz_data
        import repository.shelter_ownerships as ownerships_data
        from utils.logger import logger

        report = {
            "users_processed": 0,
            "shelters_processed": 0,
            "platform_assignments_created": 0,
            "platform_assignments_existing": 0,
            "shelter_pairs_synced": 0,
            "ownerships_created": 0,
            "ownerships_existing": 0,
            "invalid_rows": 0,
            "duplicate_legacy_roles": 0,
            "errors": 0,
        }

        # --- platform roles -------------------------------------------------
        platform_user = authz_data.get_role_by_code("PLATFORM_USER")
        platform_admin = authz_data.get_role_by_code("PLATFORM_ADMIN")
        if not platform_user or not platform_admin:
            raise click.ClickException("system roles missing — run seed-rbac first")

        for user in db.session.query(User).all():
            report["users_processed"] += 1
            try:
                _, created = authz_data.ensure_user_role(user.id, platform_user["id"])
                report["platform_assignments_created" if created else "platform_assignments_existing"] += 1
                if user.role == UserRole.ADMIN:
                    _, created = authz_data.ensure_user_role(user.id, platform_admin["id"])
                    report["platform_assignments_created" if created else "platform_assignments_existing"] += 1
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                report["errors"] += 1
                logger.error(f"backfill platform roles failed user={user.id}: {e}")

        # --- shelter roles + ownership, transactional per shelter -----------
        rows = [
            r for r in db.session.query(ShelterRole).all()
            if r.user_id and r.shelter_id
        ]
        report["invalid_rows"] = (
            db.session.query(ShelterRole).count() - len(rows)
        )
        by_shelter = {}
        for r in rows:
            by_shelter.setdefault(r.shelter_id, []).append(r)

        for shelter_id, shelter_rows in sorted(by_shelter.items()):
            report["shelters_processed"] += 1
            seen_pairs = set()
            try:
                for r in shelter_rows:
                    pair = (r.user_id, r.shelter_id)
                    if pair in seen_pairs:
                        report["duplicate_legacy_roles"] += 1
                        continue
                    seen_pairs.add(pair)
                    # sync resolves ALL legacy rows of the pair at once, so a
                    # user with duplicates still gets one assignment per level
                    authz_data.sync_legacy_shelter_role(r.user_id, r.shelter_id)
                    report["shelter_pairs_synced"] += 1
                for r in shelter_rows:
                    if r.role == RoleLevel.OWNER:
                        _, created = ownerships_data.create_ownership(
                            shelter_id=r.shelter_id,
                            user_id=r.user_id,
                            source="MIGRATION",
                            commit=False,
                        )
                        report["ownerships_created" if created else "ownerships_existing"] += 1
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                report["errors"] += 1
                logger.error(f"backfill failed shelter={shelter_id}: {e}")

        for key, value in report.items():
            click.echo(f"{key}: {value}")
        if report["errors"]:
            raise click.ClickException("backfill finished with errors — see logs")
        click.echo("rbac backfill complete")

    @app.cli.command("diagnose-rbac")
    def diagnose_rbac():
        """Pre-cutover data diagnostics. Read-only: reports anomalies and
        exits non-zero when a blocking condition (e.g. shelter without any
        valid owner) is found. Never auto-fixes ambiguous data."""
        from collections import Counter
        from repository import db
        from repository.shelter_roles.models import ShelterRole, RoleLevel
        from repository.shelters.models import Shelter
        from repository.users.models import User, UserRole
        from repository.authorization.models import (
            ShelterMembership, ShelterMembershipStatus,
            UserRoleAssignment, UserRoleStatus, Role, RbacScopeType,
        )
        from repository.shelter_ownerships.models import (
            ShelterOwnership, ShelterOwnershipStatus,
        )
        from utils.dates import utc_now

        blockers = []
        warnings = []

        shelter_ids = {s.id for s in db.session.query(Shelter.id).all()}
        user_ids = {u.id for u in db.session.query(User.id).all()}
        legacy_rows = db.session.query(ShelterRole).all()

        # legacy anomalies -----------------------------------------------------
        owners_by_shelter = Counter(
            r.shelter_id for r in legacy_rows if r.role == RoleLevel.OWNER
        )
        no_owner = shelter_ids - set(owners_by_shelter)
        multi_owner = {s for s, n in owners_by_shelter.items() if n > 1}
        if no_owner:
            warnings.append(f"{len(no_owner)} shelter(s) without a legacy OWNER: {sorted(no_owner)[:10]}")
        if multi_owner:
            warnings.append(f"{len(multi_owner)} shelter(s) with multiple legacy OWNERs: {sorted(multi_owner)[:10]}")

        pair_counter = Counter((r.user_id, r.shelter_id) for r in legacy_rows)
        dupes = [p for p, n in pair_counter.items() if n > 1]
        if dupes:
            warnings.append(f"{len(dupes)} duplicated legacy (user, shelter) pair(s): {dupes[:10]}")

        invalid = [r.id for r in legacy_rows if not r.user_id or not r.shelter_id or r.role is None]
        if invalid:
            warnings.append(f"{len(invalid)} invalid legacy shelter_roles row(s): {invalid[:10]}")

        orphan_user = [r.id for r in legacy_rows if r.user_id and r.user_id not in user_ids]
        orphan_shelter = [r.id for r in legacy_rows if r.shelter_id and r.shelter_id not in shelter_ids]
        if orphan_user or orphan_shelter:
            warnings.append(
                f"legacy rows referencing missing user ({len(orphan_user)}) "
                f"or shelter ({len(orphan_shelter)})"
            )

        # membership anomalies -------------------------------------------------
        memberships = db.session.query(ShelterMembership).all()
        active_assignment_pairs = {
            (a.user_id, a.shelter_id)
            for a in db.session.query(UserRoleAssignment).filter(
                UserRoleAssignment.status == UserRoleStatus.ACTIVE,
                UserRoleAssignment.shelter_id.isnot(None),
            ).all()
        }
        membership_no_role = [
            (m.user_id, m.shelter_id) for m in memberships
            if m.status == ShelterMembershipStatus.ACTIVE
            and (m.user_id, m.shelter_id) not in active_assignment_pairs
        ]
        if membership_no_role:
            warnings.append(
                f"{len(membership_no_role)} ACTIVE membership(s) without any active "
                f"shelter assignment: {membership_no_role[:10]}"
            )

        legacy_owner_membership = {
            (r.user_id, r.shelter_id) for r in legacy_rows if r.role == RoleLevel.OWNER
        }
        membership_by_pair = {(m.user_id, m.shelter_id): m for m in memberships}
        owner_no_membership = [
            p for p in legacy_owner_membership if p not in membership_by_pair
        ]
        owner_inactive_membership = [
            p for p in legacy_owner_membership
            if p in membership_by_pair
            and membership_by_pair[p].status != ShelterMembershipStatus.ACTIVE
        ]
        if owner_no_membership:
            warnings.append(f"{len(owner_no_membership)} legacy OWNER(s) without membership (backfill will create it)")
        if owner_inactive_membership:
            blockers.append(f"{len(owner_inactive_membership)} legacy OWNER(s) with non-ACTIVE membership: {owner_inactive_membership[:10]}")

        # RBAC assignment anomalies --------------------------------------------
        assignments = db.session.query(UserRoleAssignment).all()
        roles_by_id = {r.id: r for r in db.session.query(Role).all()}
        now = utc_now()
        shelter_scope_null = []
        platform_scope_with_shelter = []
        active_expired = []
        for a in assignments:
            role = roles_by_id.get(a.role_id)
            if role is None:
                continue
            if role.scope_type == RbacScopeType.SHELTER and a.shelter_id is None:
                shelter_scope_null.append(a.id)
            if role.scope_type == RbacScopeType.PLATFORM and a.shelter_id is not None:
                platform_scope_with_shelter.append(a.id)
            if a.status == UserRoleStatus.ACTIVE and a.valid_until and a.valid_until <= now:
                active_expired.append(a.id)
        if shelter_scope_null:
            blockers.append(f"{len(shelter_scope_null)} SHELTER assignment(s) with NULL shelter_id: {shelter_scope_null[:10]}")
        if platform_scope_with_shelter:
            blockers.append(f"{len(platform_scope_with_shelter)} PLATFORM assignment(s) with shelter_id: {platform_scope_with_shelter[:10]}")
        if active_expired:
            warnings.append(f"{len(active_expired)} ACTIVE assignment(s) past valid_until (deny at runtime): {active_expired[:10]}")

        # ownership coverage (post-backfill gate) --------------------------------
        active_ownerships = db.session.query(ShelterOwnership).filter(
            ShelterOwnership.status == ShelterOwnershipStatus.ACTIVE,
        ).all()
        owned_shelters = {o.shelter_id for o in active_ownerships}
        legacy_owner_shelters = set(owners_by_shelter)
        missing_ownership = legacy_owner_shelters - owned_shelters
        if missing_ownership:
            blockers.append(
                f"{len(missing_ownership)} shelter(s) with a legacy OWNER but no ACTIVE "
                f"ShelterOwnership (run backfill-rbac): {sorted(missing_ownership)[:10]}"
            )
        shelters_never_owned = shelter_ids - owned_shelters - legacy_owner_shelters
        if shelters_never_owned:
            blockers.append(
                f"{len(shelters_never_owned)} shelter(s) with NO owner in either system "
                f"(manual review required): {sorted(shelters_never_owned)[:10]}"
            )

        # platform role coverage --------------------------------------------------
        platform_user_role = db.session.query(Role).filter(Role.code == "PLATFORM_USER").first()
        platform_admin_role = db.session.query(Role).filter(Role.code == "PLATFORM_ADMIN").first()
        if platform_user_role:
            covered = {
                a.user_id for a in assignments
                if a.role_id == platform_user_role.id and a.status == UserRoleStatus.ACTIVE
            }
            missing = user_ids - covered
            if missing:
                blockers.append(f"{len(missing)} user(s) without PLATFORM_USER (run backfill-rbac)")
        if platform_admin_role:
            admin_users = {
                u.id for u in db.session.query(User).filter(User.role == UserRole.ADMIN).all()
            }
            covered = {
                a.user_id for a in assignments
                if a.role_id == platform_admin_role.id and a.status == UserRoleStatus.ACTIVE
            }
            missing = admin_users - covered
            if missing:
                blockers.append(f"{len(missing)} legacy ADMIN(s) without PLATFORM_ADMIN (run backfill-rbac)")

        for w in warnings:
            click.echo(f"WARNING: {w}")
        for b in blockers:
            click.echo(f"BLOCKER: {b}")
        click.echo(
            f"diagnose-rbac: {len(warnings)} warning(s), {len(blockers)} blocker(s)"
        )
        if blockers:
            raise click.ClickException("cutover blocked — resolve blockers first")
        click.echo("no blocking anomalies — cutover allowed")
