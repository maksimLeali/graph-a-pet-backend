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
        """Mirror every legacy ShelterRole row into RBAC assignments and
        memberships (idempotent; run seed-rbac first). Repairs users created
        before the automatic sync on ShelterRole create/update/delete."""
        from repository import db
        from repository.shelter_roles.models import ShelterRole
        import repository.authorization as authz_data

        pairs = {
            (r.user_id, r.shelter_id)
            for r in db.session.query(ShelterRole).all()
            if r.user_id and r.shelter_id
        }
        for user_id, shelter_id in sorted(pairs):
            authz_data.sync_legacy_shelter_role(user_id, shelter_id)
        click.echo(f"rbac backfill complete: {len(pairs)} (user, shelter) pair(s)")
