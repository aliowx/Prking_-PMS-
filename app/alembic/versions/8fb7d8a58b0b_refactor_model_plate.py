"""refactor model plate

Revision ID: 8fb7d8a58b0b
Revises: 975642ca3129
Create Date: 2024-06-29 12:25:52.788097

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fb7d8a58b0b'
down_revision = '975642ca3129'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('platedetected', sa.Column('type_status_parkinglot', sa.String(), nullable=True))
    op.add_column('record', sa.Column('plate', sa.String(), nullable=True))
    op.add_column('record', sa.Column('best_plate_image_id', sa.Integer(), nullable=True))
    op.add_column('record', sa.Column('zone_id', sa.Integer(), nullable=True))
    op.add_column('record', sa.Column('parking_lot_id', sa.Integer(), nullable=True))
    op.drop_index('ix_record_best_big_image_id', table_name='record')
    op.drop_index('ix_record_ocr', table_name='record')
    op.create_index(op.f('ix_record_best_plate_image_id'), 'record', ['best_plate_image_id'], unique=False)
    op.create_index(op.f('ix_record_parking_lot_id'), 'record', ['parking_lot_id'], unique=False)
    op.create_index(op.f('ix_record_plate'), 'record', ['plate'], unique=False)
    op.create_index(op.f('ix_record_zone_id'), 'record', ['zone_id'], unique=False)
    op.drop_constraint('record_best_big_image_id_fkey', 'record', type_='foreignkey')
    op.create_foreign_key(None, 'record', 'image', ['best_plate_image_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key(None, 'record', 'parkingzone', ['zone_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.create_foreign_key(None, 'record', 'parkinglot', ['parking_lot_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.drop_column('record', 'ocr')
    op.drop_column('record', 'best_big_image_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('record', sa.Column('best_big_image_id', sa.INTEGER(), autoincrement=False, nullable=True))
    op.add_column('record', sa.Column('ocr', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'record', type_='foreignkey')
    op.drop_constraint(None, 'record', type_='foreignkey')
    op.drop_constraint(None, 'record', type_='foreignkey')
    op.create_foreign_key('record_best_big_image_id_fkey', 'record', 'image', ['best_big_image_id'], ['id'], onupdate='CASCADE', ondelete='SET NULL')
    op.drop_index(op.f('ix_record_zone_id'), table_name='record')
    op.drop_index(op.f('ix_record_plate'), table_name='record')
    op.drop_index(op.f('ix_record_parking_lot_id'), table_name='record')
    op.drop_index(op.f('ix_record_best_plate_image_id'), table_name='record')
    op.create_index('ix_record_ocr', 'record', ['ocr'], unique=False)
    op.create_index('ix_record_best_big_image_id', 'record', ['best_big_image_id'], unique=False)
    op.drop_column('record', 'parking_lot_id')
    op.drop_column('record', 'zone_id')
    op.drop_column('record', 'best_plate_image_id')
    op.drop_column('record', 'plate')
    op.drop_column('platedetected', 'type_status_parkinglot')
    # ### end Alembic commands ###
