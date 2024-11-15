"""add AuthOTP

Revision ID: 770de711d14a
Revises: d1ed1a9658ae
Create Date: 2024-11-15 12:14:00.968996

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '770de711d14a'
down_revision = 'd1ed1a9658ae'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('authotp',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('code', sa.Integer(), nullable=True),
    sa.Column('expire_at', sa.DateTime(timezone=None), nullable=True),
    sa.Column('is_used', sa.Boolean(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('modified', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_authotp_code'), 'authotp', ['code'], unique=False)
    op.create_index(op.f('ix_authotp_created'), 'authotp', ['created'], unique=False)
    op.create_index(op.f('ix_authotp_expire_at'), 'authotp', ['expire_at'], unique=False)
    op.create_index(op.f('ix_authotp_id'), 'authotp', ['id'], unique=False)
    op.create_index(op.f('ix_authotp_is_deleted'), 'authotp', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_authotp_modified'), 'authotp', ['modified'], unique=False)
    op.create_index(op.f('ix_authotp_phone_number'), 'authotp', ['phone_number'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_authotp_phone_number'), table_name='authotp')
    op.drop_index(op.f('ix_authotp_modified'), table_name='authotp')
    op.drop_index(op.f('ix_authotp_is_deleted'), table_name='authotp')
    op.drop_index(op.f('ix_authotp_id'), table_name='authotp')
    op.drop_index(op.f('ix_authotp_expire_at'), table_name='authotp')
    op.drop_index(op.f('ix_authotp_created'), table_name='authotp')
    op.drop_index(op.f('ix_authotp_code'), table_name='authotp')
    op.drop_table('authotp')
    # ### end Alembic commands ###
