"""add_cron_fields_to_workflow

Revision ID: add_cron_fields_to_workflow
Revises: af49ca791fc7
Create Date: 2025-05-30 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_cron_fields_to_workflow'
down_revision = 'af49ca791fc7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('workflows', sa.Column('cron_schedule', sa.String(), nullable=True))
    op.add_column('workflows', sa.Column('cron_enabled', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('workflows', sa.Column('timezone', sa.String(), server_default='UTC', nullable=False))


def downgrade():
    op.drop_column('workflows', 'timezone')
    op.drop_column('workflows', 'cron_enabled')
    op.drop_column('workflows', 'cron_schedule')
