"""fix forced happy_hours time

Revision ID: 72095ffc9bf6
Revises: 5663faa686de
Create Date: 2022-07-05 18:30:17.060349

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72095ffc9bf6'
down_revision = '5663faa686de'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE warehouse_forced_happy_hours DROP COLUMN start_time;
    """)
    op.execute("""
        ALTER TABLE warehouse_forced_happy_hours ADD COLUMN start_time TIMESTAMP WITHOUT TIME ZONE NOT NULL;
    """)

    op.execute("""
            ALTER TABLE warehouse_forced_happy_hours DROP COLUMN end_time;
        """)
    op.execute("""
            ALTER TABLE warehouse_forced_happy_hours ADD COLUMN end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL;
        """)


def downgrade():
    pass
