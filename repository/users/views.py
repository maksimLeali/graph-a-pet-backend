from repository import db, ViewBase,schema

class UserPetsInCustody(ViewBase):
    __tablename__ = 'user_pets_in_custody'
    user_id = db.Column(db.String, primary_key= True)
    total= db.Column(db.Integer)
    owned_pets= db.Column(db.Integer)
    total_on_loan= db.Column(db.Integer)
    pet_sitting= db.Column(db.Integer)
    sub_owner= db.Column(db.Integer)
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "total": self.total,
            "owned_pets": self.owned_pets,
            "total_on_loan": self.total_on_loan,
            "pet_sitting": self.pet_sitting,
            "sub_owner": self.sub_owner
        }


_prefix = f"{schema}." if schema and len(schema) > 0 else ""

view_declaration = f"""
CREATE OR REPLACE VIEW {_prefix}user_pets_in_custody AS
WITH total_pets_in_custody AS (
	SELECT
		usr.id AS user_id,
		count(ows.id) AS n_pets
	FROM
		{_prefix}users usr
	LEFT JOIN {_prefix}ownerships ows ON ows.user_id = usr.id
	GROUP BY
		usr.id
),
owned_pets AS (
	SELECT
		usr.id AS user_id,
		count(ows.id) AS n_pets
	FROM
		{_prefix}users usr
	LEFT JOIN {_prefix}ownerships ows ON ows.user_id = usr.id
	WHERE
		ows.custody_level = 'OWNER'
	GROUP BY
		usr.id
),
total_pets_on_loan AS (
	SELECT
		usr.id AS user_id,
		count(ows.id) AS n_pets
	FROM
		{_prefix}users usr
	LEFT JOIN {_prefix}ownerships ows ON ows.user_id = usr.id
	WHERE
		ows.custody_level != 'OWNER'
	GROUP BY
		usr.id
),
total_pets_sitting AS (
	SELECT
		usr.id AS user_id,
		count(ows.id) AS n_pets
	FROM
		{_prefix}users usr
	LEFT JOIN {_prefix}ownerships ows ON ows.user_id = usr.id
	WHERE
		ows.custody_level = 'PET_SITTER'
	GROUP BY
		usr.id
),
total_sub_owner AS (
	SELECT
		usr.id AS user_id,
		count(ows.id) AS n_pets
	FROM
		{_prefix}users usr
	LEFT JOIN {_prefix}ownerships ows ON ows.user_id = usr.id
	WHERE
		ows.custody_level = 'SUB_OWNER'
	GROUP BY
		usr.id
)
SELECT
	usr.id as user_id,
	COALESCE(tpic.n_pets, 0) AS total,
	COALESCE(op.n_pets, 0) AS owned_pets,
	COALESCE(tpol.n_pets, 0) AS total_on_loan,
	COALESCE(tps.n_pets, 0) AS pet_sitting,
	COALESCE(tso.n_pets, 0) AS sub_owner
FROM
	{_prefix}users usr
	LEFT JOIN total_pets_in_custody tpic ON tpic.user_id = usr.id
	LEFT JOIN owned_pets op on op.user_id = usr.id
	LEFT JOIN total_pets_on_loan tpol on tpol.user_id = usr.id
	LEFT JOIN total_pets_sitting tps on tps.user_id = usr.id
	LEFT JOIN total_sub_owner tso on tso.user_id = usr.id;

"""

view_drop = f"DROP VIEW IF EXISTS {_prefix}user_pets_in_custody;"