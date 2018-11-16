"""empty message

Revision ID: 5d4aee209354
Revises: 99cd2a081a3c
Create Date: 2018-11-16 15:15:44.885014

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '5d4aee209354'
down_revision = '99cd2a081a3c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ##
    op.alter_column('dogma_attributes', 'value',
               existing_type=sa.Integer(),
               type_=sa.Float(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ##
    op.alter_column('dogma_attributes', 'value',
               existing_type=sa.Float(),
               type_=sa.Integer(),
               existing_nullable=True)
    # ### end Alembic commands ###
