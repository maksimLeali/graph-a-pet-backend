from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB
from repository import db, Base


class RbacScopeType(Enum):
    PLATFORM = "PLATFORM"
    SHELTER = "SHELTER"


class UserRoleStatus(Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class ShelterMembershipStatus(Enum):
    INVITED = "INVITED"
    PENDING_ONBOARDING = "PENDING_ONBOARDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    LEFT = "LEFT"
    REVOKED = "REVOKED"


class ShelterMembershipSource(Enum):
    INVITE = "INVITE"
    JOIN_REQUEST = "JOIN_REQUEST"
    CLAIM = "CLAIM"
    OWNERSHIP_TRANSFER = "OWNERSHIP_TRANSFER"
    MANUAL = "MANUAL"
    WORKSPACE_CREATOR = "WORKSPACE_CREATOR"


class Permission(Base):
    __tablename__ = "permissions"
    key = db.Column(db.String, nullable=False, unique=True, index=True)
    domain = db.Column(db.String, nullable=False)
    action = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    scope_type = db.Column(db.Enum(RbacScopeType), nullable=False)
    risk_level = db.Column(db.String, nullable=False, default="LOW")

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "domain": self.domain,
            "action": self.action,
            "description": self.description,
            "scope_type": self.scope_type.name if self.scope_type else None,
            "risk_level": self.risk_level,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }


class Role(Base):
    __tablename__ = "roles"
    code = db.Column(db.String, nullable=False, unique=True, index=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    scope_type = db.Column(db.Enum(RbacScopeType), nullable=False)
    owner_shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=True, index=True)
    is_system = db.Column(db.Boolean, nullable=False, default=False)
    is_assignable = db.Column(db.Boolean, nullable=False, default=True)
    grants_all_permissions = db.Column(db.Boolean, nullable=False, default=False)
    archived_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "scope_type": self.scope_type.name if self.scope_type else None,
            "owner_shelter_id": self.owner_shelter_id,
            "is_system": self.is_system,
            "is_assignable": self.is_assignable,
            "grants_all_permissions": self.grants_all_permissions,
            "archived_at": str(self.archived_at) if self.archived_at else None,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        db.UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_permission"),
        Base.__table_args__,
    )
    role_id = db.Column(db.String, db.ForeignKey("roles.id"), nullable=False, index=True)
    permission_id = db.Column(db.String, db.ForeignKey("permissions.id"), nullable=False, index=True)
    granted_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "role_id": self.role_id,
            "permission_id": self.permission_id,
            "granted_by_id": self.granted_by_id,
            "created_at": str(self.created_at),
        }


class UserRoleAssignment(Base):
    """RBAC assignment of a role to a user, optionally scoped to a shelter.

    Named UserRoleAssignment (table `user_roles`) to avoid clashing with the
    legacy `UserRole` enum in repository.users.models.
    """
    __tablename__ = "user_roles"
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False, index=True)
    role_id = db.Column(db.String, db.ForeignKey("roles.id"), nullable=False, index=True)
    shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=True, index=True)
    status = db.Column(db.Enum(UserRoleStatus), nullable=False, default=UserRoleStatus.ACTIVE, index=True)
    valid_from = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    assigned_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    revoked_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role_id": self.role_id,
            "shelter_id": self.shelter_id,
            "status": self.status.name if self.status else None,
            "valid_from": str(self.valid_from) if self.valid_from else None,
            "valid_until": str(self.valid_until) if self.valid_until else None,
            "assigned_by_id": self.assigned_by_id,
            "revoked_by_id": self.revoked_by_id,
            "revoked_at": str(self.revoked_at) if self.revoked_at else None,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }


class ShelterMembership(Base):
    __tablename__ = "shelter_memberships"
    __table_args__ = (
        db.UniqueConstraint("shelter_id", "user_id", name="uq_shelter_memberships_shelter_user"),
        Base.__table_args__,
    )
    shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=False, index=True)
    user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.Enum(ShelterMembershipStatus), nullable=False,
                       default=ShelterMembershipStatus.ACTIVE, index=True)
    source = db.Column(db.Enum(ShelterMembershipSource), nullable=False,
                       default=ShelterMembershipSource.MANUAL)
    invited_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    approved_by_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    joined_at = db.Column(db.DateTime, nullable=True)
    suspended_at = db.Column(db.DateTime, nullable=True)
    left_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "shelter_id": self.shelter_id,
            "user_id": self.user_id,
            "status": self.status.name if self.status else None,
            "source": self.source.name if self.source else None,
            "invited_by_id": self.invited_by_id,
            "approved_by_id": self.approved_by_id,
            "joined_at": str(self.joined_at) if self.joined_at else None,
            "suspended_at": str(self.suspended_at) if self.suspended_at else None,
            "left_at": str(self.left_at) if self.left_at else None,
            "revoked_at": str(self.revoked_at) if self.revoked_at else None,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }


class AuthorizationAuditLog(Base):
    __tablename__ = "authorization_audit_logs"
    actor_user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True, index=True)
    target_user_id = db.Column(db.String, db.ForeignKey("users.id"), nullable=True)
    shelter_id = db.Column(db.String, db.ForeignKey("shelters.id"), nullable=True, index=True)
    role_id = db.Column(db.String, db.ForeignKey("roles.id"), nullable=True)
    permission_id = db.Column(db.String, db.ForeignKey("permissions.id"), nullable=True)
    action = db.Column(db.String, nullable=False, index=True)
    before_data = db.Column(JSONB, nullable=True)
    after_data = db.Column(JSONB, nullable=True)
    request_id = db.Column(db.String, nullable=True)
    meta = db.Column("metadata", JSONB, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "actor_user_id": self.actor_user_id,
            "target_user_id": self.target_user_id,
            "shelter_id": self.shelter_id,
            "role_id": self.role_id,
            "permission_id": self.permission_id,
            "action": self.action,
            "before_data": self.before_data,
            "after_data": self.after_data,
            "request_id": self.request_id,
            "metadata": self.meta,
            "created_at": str(self.created_at),
        }
