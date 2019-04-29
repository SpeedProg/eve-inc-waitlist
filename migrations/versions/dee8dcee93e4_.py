"""empty message

Revision ID: dee8dcee93e4
Revises: 5d4aee209354
Create Date: 2019-04-26 15:54:00.665467

"""
from alembic import op
import sqlalchemy as sa
from waitlist.storage.database import WaitlistGroup, MarketGroup, InvGroup, InvCategory, InvType
from waitlist.base import db
from waitlist.utility.sde import update_invtypes

# revision identifiers, used by Alembic.
revision = 'dee8dcee93e4'
down_revision = 'afa58b54a8fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ship_check_collection',
    sa.Column('collection_id', sa.Integer(), nullable=False),
    sa.Column('collection_name', sa.String(length=50), nullable=True),
    sa.Column('waitlist_group_id', sa.Integer(), nullable=True),
    sa.Column('default_target_id', sa.Integer(), nullable=True),
    sa.Column('default_tag', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['default_target_id'], ['waitlists.id'], name=op.f('fk_ship_check_collection_default_target_id_waitlists'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['waitlist_group_id'], ['waitlist_groups.group_id'], name=op.f('fk_ship_check_collection_waitlist_group_id_waitlist_groups'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('collection_id', name=op.f('pk_ship_check_collection')),
    sa.UniqueConstraint('waitlist_group_id', name=op.f('uq_ship_check_collection_waitlist_group_id'))
    )
    op.create_table('ship_check',
    sa.Column('check_id', sa.Integer(), nullable=False),
    sa.Column('check_name', sa.String(length=100), nullable=True),
    sa.Column('collection_id', sa.Integer(), nullable=True),
    sa.Column('check_target_id', sa.Integer(), nullable=False),
    sa.Column('check_type', sa.Integer(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.Column('modifier', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('tag', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['check_target_id'], ['waitlists.id'], name=op.f('fk_ship_check_check_target_id_waitlists'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['collection_id'], ['ship_check_collection.collection_id'], name=op.f('fk_ship_check_collection_id_ship_check_collection'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('check_id', name=op.f('pk_ship_check'))
    )
    op.create_table('ship_check_groups',
    sa.Column('check_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['check_id'], ['ship_check.check_id'], name=op.f('fk_ship_check_groups_check_id_ship_check'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['invgroup.group_id'], name=op.f('fk_ship_check_groups_group_id_invgroup'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('ship_check_invtypes',
    sa.Column('check_id', sa.Integer(), nullable=True),
    sa.Column('type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['check_id'], ['ship_check.check_id'], name=op.f('fk_ship_check_invtypes_check_id_ship_check'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['type_id'], ['invtypes.type_id'], name=op.f('fk_ship_check_invtypes_type_id_invtypes'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('ship_check_marketgroups',
    sa.Column('check_id', sa.Integer(), nullable=True),
    sa.Column('market_group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['check_id'], ['ship_check.check_id'], name=op.f('fk_ship_check_marketgroups_check_id_ship_check'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['market_group_id'], ['invmarketgroups.market_group_id'], name=op.f('fk_ship_check_marketgroups_market_group_id_invmarketgroups'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('ship_check_rest_groups',
    sa.Column('check_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['check_id'], ['ship_check.check_id'], name=op.f('fk_ship_check_rest_groups_check_id_ship_check'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['invgroup.group_id'], name=op.f('fk_ship_check_rest_groups_group_id_invgroup'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('ship_check_rest_invtypes',
    sa.Column('check_id', sa.Integer(), nullable=True),
    sa.Column('type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['check_id'], ['ship_check.check_id'], name=op.f('fk_ship_check_rest_invtypes_check_id_ship_check'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['type_id'], ['invtypes.type_id'], name=op.f('fk_ship_check_rest_invtypes_type_id_invtypes'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('ship_check_rest_marketgroups',
    sa.Column('check_id', sa.Integer(), nullable=True),
    sa.Column('market_group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['check_id'], ['ship_check.check_id'], name=op.f('fk_ship_check_rest_marketgroups_check_id_ship_check'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['market_group_id'], ['invmarketgroups.market_group_id'], name=op.f('fk_ship_check_rest_marketgroups_market_group_id_invmarketgroups'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.add_column('fittings', sa.Column('target_waitlist', sa.Integer(), nullable=True))
    op.create_foreign_key(op.f('fk_fittings_target_waitlist_waitlists'), 'fittings', 'waitlists', ['target_waitlist'], ['id'], onupdate='CASCADE', ondelete='CASCADE')

    op.add_column('waitlist_groups', sa.Column('queueID', sa.Integer(), nullable=True))
    wl_groups = db.session.query(WaitlistGroup).all()
    for wl_group in wl_groups:
        queue_wl = None
        for wl in wl_group.waitlists:
            if wl.waitlistType == "xup":
                queue_wl = wl
                break
        if queue_wl is None:
            print("There is an error with your database, waitlist group", wl_group.groupID, "is missing an xup list")
        else:
            wl_group.queueID = queue_wl.id
    db.session.commit()
    # now we can remove the nullable=True
    op.alter_column('waitlist_groups', 'queueID', existing_type=sa.Integer(), nullable=False)
    op.create_foreign_key(op.f('fk_waitlist_groups_queueID_waitlists'), 'waitlist_groups', 'waitlists', ['queueID'], ['id'])
    op.alter_column('fittings', 'wl_type',
                    existing_type=sa.String(length=10),
                    type_=sa.String(length=20),
                    existing_nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('fittings', 'wl_type',
                    existing_type=sa.String(length=20),
                    type_=sa.String(length=10),
                    existing_nullable=True)
    op.drop_constraint(op.f('fk_waitlist_groups_queueID_waitlists'), 'waitlist_groups', type_='foreignkey')
    op.drop_column('waitlist_groups', 'queueID')
    op.drop_constraint(op.f('fk_fittings_target_waitlist_waitlists'), 'fittings', type_='foreignkey')
    op.drop_column('fittings', 'target_waitlist')
    op.drop_table('ship_check_rest_marketgroups')
    op.drop_table('ship_check_rest_invtypes')
    op.drop_table('ship_check_rest_groups')
    op.drop_table('ship_check_marketgroups')
    op.drop_table('ship_check_invtypes')
    op.drop_table('ship_check_groups')
    op.drop_table('ship_check_collection')
    op.drop_table('ship_check')
    # ### end Alembic commands ###
