"""parking_payment_type

Revision ID: 0d3dbb238810
Revises: 112ab03ed0fd
Create Date: 2024-06-01 13:04:55.850885

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0d3dbb238810'
down_revision = '112ab03ed0fd'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('parking', sa.Column('payment_type', sa.Integer(), nullable=True))
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
    op.drop_column('parking', 'payment_type')
    # ### end Alembic commands ###
