"""added earned, accepted_answer

Revision ID: 092344d4ec34
Revises: e3116f23644e
Create Date: 2016-01-26 21:59:41.298191

"""

# revision identifiers, used by Alembic.
revision = '092344d4ec34'
down_revision = 'e3116f23644e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('questions', sa.Column('accepted_answer', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'questions', 'answers', ['accepted_answer'], ['id'])
    op.add_column('users', sa.Column('earned', sa.Integer(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'earned')
    op.drop_constraint(None, 'questions', type_='foreignkey')
    op.drop_column('questions', 'accepted_answer')
    ### end Alembic commands ###
