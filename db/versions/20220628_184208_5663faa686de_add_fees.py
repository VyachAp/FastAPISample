"""add fees

Revision ID: 5663faa686de
Revises: 
Create Date: 2022-06-24 15:00:14.490630

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5663faa686de'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TYPE FEE_TYPE AS ENUM('packaging', 'delivery', 'custom');
    """)
    op.execute("""
        CREATE TABLE fees (
            id UUID PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            value INT NOT NULL,
            img_url TEXT,
            fee_type FEE_TYPE NOT NULL,
            free_after_subtotal INT,
            active BOOLEAN NOT NULL DEFAULT FALSE
        );"""
    )
    op.execute("""
        CREATE TABLE user_fees (
            user_id UUID,
            fee_id UUID REFERENCES fees(id),
            PRIMARY KEY (user_id, fee_id)
        );
    """)
    op.execute("""
        CREATE TABLE warehouse_fees (
            warehouse_id UUID,
            fee_id UUID REFERENCES fees(id),
            PRIMARY KEY (warehouse_id, fee_id)
        );
    """)
    op.execute("""
        CREATE TABLE warehouse_happy_hours (
            warehouse_id UUID,
            weekday INT NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            value INT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (warehouse_id, weekday, start_time)
        );
    """)
    op.execute("""
        CREATE TABLE warehouse_forced_happy_hours (
            warehouse_id UUID,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            value INT NOT NULL,
            active BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (warehouse_id, start_time)
        );
    """)
    op.execute("""
        CREATE TABLE warehouse_bonus_settings (
            warehouse_id UUID PRIMARY KEY,
            required_subtotal INT NOT NULL,
            bonus_fixed INT,
            bonus_percent INT,
            active BOOLEAN NOT NULL DEFAULT FALSE
        );
    """)


def downgrade():
    pass
