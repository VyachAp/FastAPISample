"""rename delivery fee

Revision ID: 9edc5dcd3196
Revises: 410f3d5f170f
Create Date: 2022-08-10 18:12:16.641846

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9edc5dcd3196'
down_revision = '410f3d5f170f'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TYPE FEE_TYPE ADD VALUE 'small_order';
    """)


def downgrade():
    pass
