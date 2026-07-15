"""shelter_public_story_html

Revision ID: a1b2c3d4e5f7
Revises: 486d69ff1e7c
Create Date: 2026-07-15

Adds `public_story_html` to shelters: sanitized rich-text (WYSIWYG) content
composed in the backoffice and rendered on the shelter's public profile for
external users. Stored already-sanitized (allowlist, see
utils/html_sanitize.py) so render sites can trust it; nullable, opt-in like
the other public_* profile fields.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = '486d69ff1e7c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('shelters', sa.Column('public_story_html', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('shelters', 'public_story_html')
