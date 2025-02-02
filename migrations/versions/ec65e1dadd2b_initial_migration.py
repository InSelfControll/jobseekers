"""Initial migration

Revision ID: ec65e1dadd2b
Revises: 
Create Date: 2024-12-21 02:46:22.640315

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ec65e1dadd2b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('employer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('company_name', sa.String(length=120), nullable=False),
    sa.Column('sso_domain', sa.String(length=255), nullable=True),
    sa.Column('sso_provider', sa.String(length=50), nullable=True),
    sa.Column('sso_config', sa.JSON(), nullable=True),
    sa.Column('company_domain', sa.String(length=120), nullable=True),
    sa.Column('tenant_id', sa.String(length=50), nullable=True),
    sa.Column('db_name', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=256), nullable=True),
    sa.Column('is_admin', sa.Boolean(), nullable=True),
    sa.Column('is_owner', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('email_footer', sa.Text(), nullable=True),
    sa.Column('notify_new_applications', sa.Boolean(), nullable=True),
    sa.Column('notify_status_changes', sa.Boolean(), nullable=True),
    sa.Column('ssl_enabled', sa.Boolean(), nullable=True),
    sa.Column('ssl_cert_path', sa.String(length=512), nullable=True),
    sa.Column('ssl_key_path', sa.String(length=512), nullable=True),
    sa.Column('ssl_expiry', sa.DateTime(), nullable=True),
    sa.Column('domain_verification_date', sa.DateTime(), nullable=True),
    sa.Column('domain_verified', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('sso_domain'),
    sa.UniqueConstraint('tenant_id')
    )
    op.create_table('job_seeker',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('telegram_id', sa.String(length=128), nullable=False),
    sa.Column('full_name', sa.String(length=128), nullable=False),
    sa.Column('phone_number', sa.String(length=20), nullable=False),
    sa.Column('resume_path', sa.String(length=256), nullable=True),
    sa.Column('skills', sa.JSON(), nullable=True),
    sa.Column('location', sa.String(length=128), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('telegram_id')
    )
    op.create_table('job',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('employer_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=128), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('location', sa.String(length=128), nullable=False),
    sa.Column('latitude', sa.Float(), nullable=False),
    sa.Column('longitude', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['employer_id'], ['employer.id'], name='fk_job_employer'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('application',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', sa.Integer(), nullable=False),
    sa.Column('job_seeker_id', sa.Integer(), nullable=False),
    sa.Column('cover_letter', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['job.id'], name='fk_application_job'),
    sa.ForeignKeyConstraint(['job_seeker_id'], ['job_seeker.id'], name='fk_application_job_seeker'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('application_id', sa.Integer(), nullable=False),
    sa.Column('sender_type', sa.String(length=20), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['application_id'], ['application.id'], name='fk_message_application'),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('message')
    op.drop_table('application')
    op.drop_table('job')
    op.drop_table('job_seeker')
    op.drop_table('employer')
    # ### end Alembic commands ###
