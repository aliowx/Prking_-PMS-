"""column price_model in record

Revision ID: 46bc4703a244
Revises: b2c3766591fe
Create Date: 2024-05-08 12:22:07.901491

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '46bc4703a244'
down_revision = 'b2c3766591fe'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('record', sa.Column('price_model', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('record', 'price_model')
    # ### end Alembic commands ###
