"""make bonus happy hours only

Revision ID: 410f3d5f170f
Revises: 046892de5db5
Create Date: 2022-07-20 15:51:30.102091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '410f3d5f170f'
down_revision = '046892de5db5'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE warehouse_bonus_settings ADD COLUMN happy_hours_only BOOLEAN NOT NULL DEFAULT FALSE;
    """)


def downgrade():
    pass
