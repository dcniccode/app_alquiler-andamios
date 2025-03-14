"""Agregando columna monto a cliente

Revision ID: bbbe1351dac8
Revises: 5b654acbb8fb
Create Date: 2025-02-20 19:19:49.396948

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbbe1351dac8'
down_revision = '5b654acbb8fb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cliente', schema=None) as batch_op:
        batch_op.add_column(sa.Column('monto', sa.Float(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('cliente', schema=None) as batch_op:
        batch_op.drop_column('monto')

    # ### end Alembic commands ###
