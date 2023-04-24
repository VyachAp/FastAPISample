"""split schedule and happy hours

Revision ID: 4527a75e1223
Revises: 72095ffc9bf6
Create Date: 2022-07-12 14:27:46.259948

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4527a75e1223'
down_revision = '72095ffc9bf6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE warehouse_forced_happy_hours DROP COLUMN value;
    """)
    op.execute("""
        ALTER TABLE warehouse_happy_hours DROP COLUMN value;
    """)
    op.execute("""
        CREATE TABLE warehouse_happy_hours_settings (
            warehouse_id UUID PRIMARY KEY,
            bonus_amount INT NOT NULL
        );
    """)


def downgrade():
    pass
