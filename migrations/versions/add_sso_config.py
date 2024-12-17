
"""add sso config column

Revision ID: add_sso_config
Revises: add_domain_verified
Create Date: 2024-12-17 18:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = 'add_sso_config'
down_revision = 'add_domain_verified'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('employer', schema=None) as batch_op:
        batch_op.add_column(sa.Column('sso_config', sa.JSON(), nullable=True))

def downgrade():
    with op.batch_alter_table('employer', schema=None) as batch_op:
        batch_op.drop_column('sso_config')
