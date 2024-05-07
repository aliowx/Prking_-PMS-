"""all column price in table parking

Revision ID: f362077751a2
Revises: 50d734d2441f
Create Date: 2024-05-06 15:00:14.537905

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f362077751a2'
down_revision = '50d734d2441f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('parking', sa.Column('price_model', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('parking', 'price_model')
    # ### end Alembic commands ###
