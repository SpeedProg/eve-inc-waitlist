"""empty message

Revision ID: 686609cc9783
Revises: d464aa706238
Create Date: 2017-01-30 14:58:22.760000

"""

# revision identifiers, used by Alembic.
revision = '686609cc9783'
down_revision = 'd464aa706238'

from alembic import op

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'ssotoken_ibfk_1', 'SSOToken', type_='foreignkey')
    op.create_foreign_key(None, 'SSOToken', 'accounts', ['accountID'], ['id'], onupdate='CASCADE', ondelete='CASCADE')
   # op.drop_constraint(u'tokenscope_ibfk_1', 'tokenscope', type_='foreignkey')
   # op.drop_constraint(u'tokenscope_ibfk_2', 'tokenscope', type_='foreignkey')
    op.create_foreign_key(None, 'TokenScope', 'EveApiScope', ['scopeID'], ['scopeID'], onupdate='CASCADE', ondelete='CASCADE')
    op.create_foreign_key(None, 'TokenScope', 'SSOToken', ['tokenID'], ['accountID'], onupdate='CASCADE', ondelete='CASCADE')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'tokenscope', type_='foreignkey')
    op.drop_constraint(None, 'tokenscope', type_='foreignkey')
    op.create_foreign_key(u'tokenscope_ibfk_2', 'tokenscope', 'ssotoken', ['tokenID'], ['accountID'])
    op.create_foreign_key(u'tokenscope_ibfk_1', 'tokenscope', 'eveapiscope', ['scopeID'], ['scopeID'])
    op.drop_constraint(None, 'ssotoken', type_='foreignkey')
    op.create_foreign_key(u'ssotoken_ibfk_1', 'ssotoken', 'accounts', ['accountID'], ['id'])
    ### end Alembic commands ###
