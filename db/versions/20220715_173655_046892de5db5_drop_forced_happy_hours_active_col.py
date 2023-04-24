"""drop forced happy hours active col

Revision ID: 046892de5db5
Revises: 4527a75e1223
Create Date: 2022-07-15 17:36:55.497390

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '046892de5db5'
down_revision = '4527a75e1223'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE warehouse_forced_happy_hours DROP COLUMN active;
    """)


def downgrade():
    pass
