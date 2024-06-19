"""parkingzone

Revision ID: 73a04908d735
Revises: 0d3dbb238810
Create Date: 2024-06-02 15:08:44.266378

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73a04908d735'
down_revision = '0d3dbb238810'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('parkingzone',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('tag', sa.String(length=50), nullable=True),
    sa.Column('parking_id', sa.Integer(), nullable=False),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('created', sa.DateTime(timezone=True), nullable=True),
    sa.Column('modified', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['parent_id'], ['parkingzone.id'], ),
    sa.ForeignKeyConstraint(['parent_id'], ['parkingzone.id'], initially='DEFERRED', deferrable=True),
    sa.ForeignKeyConstraint(['parking_id'], ['parking.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_parkingzone_created'), 'parkingzone', ['created'], unique=False)
    op.create_index(op.f('ix_parkingzone_id'), 'parkingzone', ['id'], unique=False)
    op.create_index(op.f('ix_parkingzone_is_deleted'), 'parkingzone', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_parkingzone_modified'), 'parkingzone', ['modified'], unique=False)
    op.alter_column('parking', 'location_lat',
               existing_type=sa.REAL(),
               type_=sa.Float(precision=7),
               existing_nullable=True)
    op.alter_column('parking', 'location_lon',
               existing_type=sa.REAL(),
               type_=sa.Float(precision=7),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('parking', 'location_lon',
               existing_type=sa.Float(precision=7),
               type_=sa.REAL(),
               existing_nullable=True)
    op.alter_column('parking', 'location_lat',
               existing_type=sa.Float(precision=7),
               type_=sa.REAL(),
               existing_nullable=True)
    op.drop_index(op.f('ix_parkingzone_modified'), table_name='parkingzone')
    op.drop_index(op.f('ix_parkingzone_is_deleted'), table_name='parkingzone')
    op.drop_index(op.f('ix_parkingzone_id'), table_name='parkingzone')
    op.drop_index(op.f('ix_parkingzone_created'), table_name='parkingzone')
    op.drop_table('parkingzone')
    # ### end Alembic commands ###
