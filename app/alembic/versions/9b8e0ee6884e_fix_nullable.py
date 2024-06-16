"""fix nullable

Revision ID: 9b8e0ee6884e
Revises: 47dca3293928
Create Date: 2024-06-16 11:51:19.403267

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b8e0ee6884e'
down_revision = '47dca3293928'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('record', 'best_lpr_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('record', 'best_big_image_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('record', 'best_big_image_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('record', 'best_lpr_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###
