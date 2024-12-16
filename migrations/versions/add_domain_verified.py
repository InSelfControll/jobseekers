
"""add domain verified column

Revision ID: add_domain_verified
Revises: 82718b7aba01
Create Date: 2024-12-16 00:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_domain_verified'
down_revision = '82718b7aba01'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('employer', sa.Column('domain_verified', sa.Boolean(), nullable=True, server_default='false'))

def downgrade():
    op.drop_column('employer', 'domain_verified')
