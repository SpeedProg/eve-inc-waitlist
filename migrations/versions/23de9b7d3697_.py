"""empty message

Revision ID: 23de9b7d3697
Revises: 
Create Date: 2018-03-02 14:05:04.480724

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '23de9b7d3697'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('apicache_allianceinfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('alliance_name', sa.String(length=100), nullable=True),
    sa.Column('date_founded', sa.DateTime(), nullable=True),
    sa.Column('executor_corp_id', sa.Integer(), nullable=True),
    sa.Column('ticker', sa.String(length=10), nullable=True),
    sa.Column('expire', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_apicache_allianceinfo'))
    )
    op.create_index(op.f('ix_apicache_allianceinfo_alliance_name'), 'apicache_allianceinfo', ['alliance_name'], unique=False)
    op.create_index(op.f('ix_apicache_allianceinfo_executor_corp_id'), 'apicache_allianceinfo', ['executor_corp_id'], unique=False)
    op.create_table('apicache_characteraffiliation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('corporation_id', sa.Integer(), nullable=True),
    sa.Column('corporation_name', sa.String(length=100), nullable=True),
    sa.Column('alliance_id', sa.Integer(), nullable=True),
    sa.Column('alliance_name', sa.String(length=100), nullable=True),
    sa.Column('expire', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_apicache_characteraffiliation'))
    )
    op.create_index(op.f('ix_apicache_characteraffiliation_alliance_id'), 'apicache_characteraffiliation', ['alliance_id'], unique=False)
    op.create_index(op.f('ix_apicache_characteraffiliation_alliance_name'), 'apicache_characteraffiliation', ['alliance_name'], unique=False)
    op.create_index(op.f('ix_apicache_characteraffiliation_corporation_id'), 'apicache_characteraffiliation', ['corporation_id'], unique=False)
    op.create_index(op.f('ix_apicache_characteraffiliation_corporation_name'), 'apicache_characteraffiliation', ['corporation_name'], unique=False)
    op.create_index(op.f('ix_apicache_characteraffiliation_name'), 'apicache_characteraffiliation', ['name'], unique=False)
    op.create_table('apicache_characterinfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('character_name', sa.String(length=100), nullable=True),
    sa.Column('corporation_id', sa.Integer(), nullable=True),
    sa.Column('character_birthday', sa.DateTime(), nullable=False),
    sa.Column('race_id', sa.Integer(), nullable=True),
    sa.Column('expire', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_apicache_characterinfo'))
    )
    op.create_index(op.f('ix_apicache_characterinfo_corporation_id'), 'apicache_characterinfo', ['corporation_id'], unique=False)
    op.create_table('apicache_corporationinfo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('alliance_id', sa.Integer(), nullable=True),
    sa.Column('ceo_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('creator_id', sa.Integer(), nullable=True),
    sa.Column('member_count', sa.Integer(), nullable=True),
    sa.Column('tax_rate', sa.Float(), nullable=True),
    sa.Column('ticker', sa.String(length=10), nullable=True),
    sa.Column('url', sa.String(length=500), nullable=True),
    sa.Column('creation_date', sa.DateTime(), nullable=True),
    sa.Column('expire', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_apicache_corporationinfo'))
    )
    op.create_index(op.f('ix_apicache_corporationinfo_alliance_id'), 'apicache_corporationinfo', ['alliance_id'], unique=False)
    op.create_index(op.f('ix_apicache_corporationinfo_name'), 'apicache_corporationinfo', ['name'], unique=False)
    op.create_table('calendar_category',
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('category_name', sa.String(length=50), nullable=True),
    sa.Column('fixed_title', sa.String(length=200), nullable=True),
    sa.Column('fixed_description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('category_id', name=op.f('pk_calendar_category'))
    )
    op.create_index(op.f('ix_calendar_category_category_name'), 'calendar_category', ['category_name'], unique=False)
    op.create_table('characters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('eve_name', sa.String(length=100), nullable=True),
    sa.Column('new_bro', sa.Boolean(name='new_bro'), nullable=False),
    sa.Column('lc_level', sa.SmallInteger(), nullable=False),
    sa.Column('cbs_level', sa.SmallInteger(), nullable=False),
    sa.Column('login_token', sa.String(length=16), nullable=True),
    sa.Column('teamspeak_poke', sa.Boolean(name='teamspeak_poke'), server_default='1', nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_characters'))
    )
    op.create_table('constellation',
    sa.Column('constellation_id', sa.Integer(), nullable=False),
    sa.Column('constellation_name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('constellation_id', name=op.f('pk_constellation'))
    )
    op.create_index(op.f('ix_constellation_constellation_name'), 'constellation', ['constellation_name'], unique=True)
    op.create_table('eveapiscope',
    sa.Column('scope_id', sa.Integer(), nullable=False),
    sa.Column('scope_name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('scope_id', name=op.f('pk_eveapiscope'))
    )
    op.create_index(op.f('ix_eveapiscope_scope_name'), 'eveapiscope', ['scope_name'], unique=False)
    op.create_table('event_history_types',
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('type_name', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('type_id', name=op.f('pk_event_history_types')),
    sa.UniqueConstraint('type_name', name=op.f('uq_event_history_types_type_name'))
    )
    op.create_table('invmarketgroups',
    sa.Column('market_group_id', sa.Integer(), nullable=False),
    sa.Column('parent_group_id', sa.Integer(), nullable=True),
    sa.Column('market_group_name', sa.String(length=100), nullable=True),
    sa.Column('description', sa.String(length=3000), nullable=True),
    sa.Column('icon_id', sa.Integer(), nullable=True),
    sa.Column('has_types', sa.Boolean(name='has_types'), nullable=True),
    sa.ForeignKeyConstraint(['parent_group_id'], ['invmarketgroups.market_group_id'], name=op.f('fk_invmarketgroups_parent_group_id_invmarketgroups')),
    sa.PrimaryKeyConstraint('market_group_id', name=op.f('pk_invmarketgroups'))
    )
    op.create_table('invtypes',
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('type_name', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('market_group_id', sa.BIGINT(), nullable=True),
    sa.PrimaryKeyConstraint('type_id', name=op.f('pk_invtypes'))
    )
    op.create_index(op.f('ix_invtypes_group_id'), 'invtypes', ['group_id'], unique=False)
    op.create_table('permissions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_permissions')),
    sa.UniqueConstraint('name', name=op.f('uq_permissions_name'))
    )
    op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('display_name', sa.String(length=150), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
    sa.UniqueConstraint('name', name=op.f('uq_roles_name'))
    )
    op.create_table('settings',
    sa.Column('key', sa.String(length=20), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_settings'))
    )
    op.create_table('solarsystem',
    sa.Column('solar_system_id', sa.Integer(), nullable=False),
    sa.Column('solar_system_name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('solar_system_id', name=op.f('pk_solarsystem'))
    )
    op.create_index(op.f('ix_solarsystem_solar_system_name'), 'solarsystem', ['solar_system_name'], unique=True)
    op.create_table('station',
    sa.Column('station_id', sa.Integer(), nullable=False),
    sa.Column('station_name', sa.String(length=100), nullable=True),
    sa.PrimaryKeyConstraint('station_id', name=op.f('pk_station'))
    )
    op.create_index(op.f('ix_station_station_name'), 'station', ['station_name'], unique=True)
    op.create_table('ts_dati',
    sa.Column('teamspeak_id', sa.Integer(), nullable=False),
    sa.Column('display_name', sa.String(length=128), nullable=True),
    sa.Column('host', sa.String(length=128), nullable=True),
    sa.Column('port', sa.Integer(), nullable=True),
    sa.Column('display_host', sa.String(length=128), nullable=True),
    sa.Column('display_port', sa.Integer(), nullable=True),
    sa.Column('query_name', sa.String(length=128), nullable=True),
    sa.Column('query_password', sa.String(length=128), nullable=True),
    sa.Column('server_id', sa.Integer(), nullable=True),
    sa.Column('channel_id', sa.Integer(), nullable=True),
    sa.Column('client_name', sa.String(length=20), nullable=True),
    sa.Column('safety_channel_id', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('teamspeak_id', name=op.f('pk_ts_dati'))
    )
    op.create_table('accounts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('current_char', sa.Integer(), nullable=True),
    sa.Column('username', sa.String(length=100), nullable=True),
    sa.Column('login_token', sa.String(length=16), nullable=True),
    sa.Column('disabled', sa.Boolean(name='disabled'), server_default=sa.text('false'), nullable=True),
    sa.Column('had_welcome_mail', sa.Boolean(name='had_welcome_mail'), server_default=sa.text('false'), nullable=True),
    sa.ForeignKeyConstraint(['current_char'], ['characters.id'], name=op.f('fk_accounts_current_char_characters')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounts')),
    sa.UniqueConstraint('login_token', name=op.f('uq_accounts_login_token')),
    sa.UniqueConstraint('username', name=op.f('uq_accounts_username'))
    )
    op.create_table('ban',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('admin', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['admin'], ['characters.id'], name=op.f('fk_ban_admin_characters')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ban'))
    )
    op.create_index(op.f('ix_ban_name'), 'ban', ['name'], unique=False)
    op.create_table('event_history_entries',
    sa.Column('history_id', sa.Integer(), nullable=False),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('type_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['type_id'], ['event_history_types.type_id'], name=op.f('fk_event_history_entries_type_id_event_history_types')),
    sa.PrimaryKeyConstraint('history_id', name=op.f('pk_event_history_entries'))
    )
    op.create_index(op.f('ix_event_history_entries_time'), 'event_history_entries', ['time'], unique=False)
    op.create_table('feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('last_changed', sa.DateTime(), nullable=True),
    sa.Column('user', sa.Integer(), nullable=True),
    sa.Column('likes', sa.Boolean(name='likes'), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user'], ['characters.id'], name=op.f('fk_feedback_user_characters')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_feedback'))
    )
    op.create_index(op.f('ix_feedback_last_changed'), 'feedback', ['last_changed'], unique=False)
    op.create_index(op.f('ix_feedback_user'), 'feedback', ['user'], unique=True)
    op.create_table('fittings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ship_type', sa.Integer(), nullable=True),
    sa.Column('modules', sa.String(length=5000), nullable=True),
    sa.Column('comment', sa.String(length=5000), nullable=True),
    sa.Column('wl_type', sa.String(length=10), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ship_type'], ['invtypes.type_id'], name=op.f('fk_fittings_ship_type_invtypes')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fittings'))
    )
    op.create_table('incursion_layout',
    sa.Column('constellation', sa.Integer(), nullable=False),
    sa.Column('staging', sa.Integer(), nullable=True),
    sa.Column('headquarter', sa.Integer(), nullable=True),
    sa.Column('dockup', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['constellation'], ['constellation.constellation_id'], name=op.f('fk_incursion_layout_constellation_constellation')),
    sa.ForeignKeyConstraint(['dockup'], ['station.station_id'], name=op.f('fk_incursion_layout_dockup_station')),
    sa.ForeignKeyConstraint(['headquarter'], ['solarsystem.solar_system_id'], name=op.f('fk_incursion_layout_headquarter_solarsystem')),
    sa.ForeignKeyConstraint(['staging'], ['solarsystem.solar_system_id'], name=op.f('fk_incursion_layout_staging_solarsystem')),
    sa.PrimaryKeyConstraint('constellation', name=op.f('pk_incursion_layout'))
    )
    op.create_table('permission_roles',
    sa.Column('permission', sa.Integer(), nullable=True),
    sa.Column('role', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['permission'], ['permissions.id'], name=op.f('fk_permission_roles_permission_permissions')),
    sa.ForeignKeyConstraint(['role'], ['roles.id'], name=op.f('fk_permission_roles_role_roles'))
    )
    op.create_table('tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=50), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('state', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], name=op.f('fk_tickets_character_id_characters')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_tickets'))
    )
    op.create_index(op.f('ix_tickets_character_id'), 'tickets', ['character_id'], unique=False)
    op.create_index(op.f('ix_tickets_state'), 'tickets', ['state'], unique=False)
    op.create_index(op.f('ix_tickets_time'), 'tickets', ['time'], unique=False)
    op.create_table('waitlist_groups',
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('group_name', sa.String(length=50), nullable=False),
    sa.Column('display_name', sa.String(length=50), nullable=False),
    sa.Column('enabled', sa.Boolean(name='enabled'), nullable=False),
    sa.Column('status', sa.String(length=1000), nullable=True),
    sa.Column('dockup_id', sa.Integer(), nullable=True),
    sa.Column('system_id', sa.Integer(), nullable=True),
    sa.Column('constellation_id', sa.Integer(), nullable=True),
    sa.Column('ordering', sa.Integer(), nullable=False),
    sa.Column('influence', sa.Boolean(name='influence'), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['constellation_id'], ['constellation.constellation_id'], name=op.f('fk_waitlist_groups_constellation_id_constellation')),
    sa.ForeignKeyConstraint(['dockup_id'], ['station.station_id'], name=op.f('fk_waitlist_groups_dockup_id_station')),
    sa.ForeignKeyConstraint(['system_id'], ['solarsystem.solar_system_id'], name=op.f('fk_waitlist_groups_system_id_solarsystem')),
    sa.PrimaryKeyConstraint('group_id', name=op.f('pk_waitlist_groups')),
    sa.UniqueConstraint('display_name', name=op.f('uq_waitlist_groups_display_name')),
    sa.UniqueConstraint('group_name', name=op.f('uq_waitlist_groups_group_name'))
    )
    op.create_table('whitelist',
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('admin_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['admin_id'], ['characters.id'], name=op.f('fk_whitelist_admin_id_characters')),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], name=op.f('fk_whitelist_character_id_characters')),
    sa.PrimaryKeyConstraint('character_id', name=op.f('pk_whitelist'))
    )
    op.create_table('account_notes',
    sa.Column('entry_id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('by_account_id', sa.Integer(), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('restriction_level', sa.SmallInteger(), server_default=sa.text('50'), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_account_notes_account_id_accounts')),
    sa.ForeignKeyConstraint(['by_account_id'], ['accounts.id'], name=op.f('fk_account_notes_by_account_id_accounts')),
    sa.PrimaryKeyConstraint('entry_id', name=op.f('pk_account_notes'))
    )
    op.create_index(op.f('ix_account_notes_time'), 'account_notes', ['time'], unique=False)
    op.create_table('account_roles',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('role_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_account_roles_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_account_roles_role_id_roles'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('backseats',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_backseats_account_id_accounts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'], name=op.f('fk_backseats_group_id_waitlist_groups'), ondelete='CASCADE')
    )
    op.create_table('calendar_event',
    sa.Column('event_id', sa.Integer(), nullable=False),
    sa.Column('event_creator_id', sa.Integer(), nullable=True),
    sa.Column('event_title', sa.Text(), nullable=True),
    sa.Column('event_description', sa.Text(), nullable=True),
    sa.Column('event_category_id', sa.Integer(), nullable=True),
    sa.Column('event_approved', sa.Boolean(name='event_approved'), nullable=True),
    sa.Column('event_time', sa.DateTime(), nullable=True),
    sa.Column('approver_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['approver_id'], ['accounts.id'], name=op.f('fk_calendar_event_approver_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_category_id'], ['calendar_category.category_id'], name=op.f('fk_calendar_event_event_category_id_calendar_category'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_creator_id'], ['accounts.id'], name=op.f('fk_calendar_event_event_creator_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('event_id', name=op.f('pk_calendar_event'))
    )
    op.create_index(op.f('ix_calendar_event_event_approved'), 'calendar_event', ['event_approved'], unique=False)
    op.create_index(op.f('ix_calendar_event_event_category_id'), 'calendar_event', ['event_category_id'], unique=False)
    op.create_index(op.f('ix_calendar_event_event_creator_id'), 'calendar_event', ['event_creator_id'], unique=False)
    op.create_index(op.f('ix_calendar_event_event_time'), 'calendar_event', ['event_time'], unique=False)
    op.create_table('ccvote',
    sa.Column('ccvote_id', sa.Integer(), nullable=False),
    sa.Column('voter_id', sa.Integer(), nullable=True),
    sa.Column('lmvote_id', sa.Integer(), nullable=True),
    sa.Column('fcvote_id', sa.Integer(), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['fcvote_id'], ['accounts.id'], name=op.f('fk_ccvote_fcvote_id_accounts')),
    sa.ForeignKeyConstraint(['lmvote_id'], ['accounts.id'], name=op.f('fk_ccvote_lmvote_id_accounts')),
    sa.ForeignKeyConstraint(['voter_id'], ['characters.id'], name=op.f('fk_ccvote_voter_id_characters')),
    sa.PrimaryKeyConstraint('ccvote_id', name=op.f('pk_ccvote'))
    )
    op.create_table('comp_history',
    sa.Column('history_id', sa.Integer(), nullable=False),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('target_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=20), nullable=True),
    sa.Column('time', sa.DateTime(), nullable=True),
    sa.Column('exref', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['source_id'], ['accounts.id'], name=op.f('fk_comp_history_source_id_accounts')),
    sa.ForeignKeyConstraint(['target_id'], ['characters.id'], name=op.f('fk_comp_history_target_id_characters')),
    sa.PrimaryKeyConstraint('history_id', name=op.f('pk_comp_history'))
    )
    op.create_index(op.f('ix_comp_history_time'), 'comp_history', ['time'], unique=False)
    op.create_table('crest_fleets',
    sa.Column('fleet_id', sa.BigInteger(), nullable=False),
    sa.Column('logi_wing_id', sa.BigInteger(), nullable=True),
    sa.Column('logi_squad_id', sa.BigInteger(), nullable=True),
    sa.Column('sniper_wing_id', sa.BigInteger(), nullable=True),
    sa.Column('sniper_squad_id', sa.BigInteger(), nullable=True),
    sa.Column('dps_wing_id', sa.BigInteger(), nullable=True),
    sa.Column('dps_squad_id', sa.BigInteger(), nullable=True),
    sa.Column('other_wing_id', sa.BigInteger(), nullable=True),
    sa.Column('other_squad_id', sa.BigInteger(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('comp_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['comp_id'], ['accounts.id'], name=op.f('fk_crest_fleets_comp_id_accounts')),
    sa.ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'], name=op.f('fk_crest_fleets_group_id_waitlist_groups')),
    sa.PrimaryKeyConstraint('fleet_id', name=op.f('pk_crest_fleets'))
    )
    op.create_table('event_history_info',
    sa.Column('info_id', sa.Integer(), nullable=False),
    sa.Column('history_id', sa.Integer(), nullable=True),
    sa.Column('info_type', sa.Integer(), nullable=True),
    sa.Column('reference_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['history_id'], ['event_history_entries.history_id'], name=op.f('fk_event_history_info_history_id_event_history_entries')),
    sa.PrimaryKeyConstraint('info_id', name=op.f('pk_event_history_info'))
    )
    op.create_table('fcs',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_fcs_account_id_accounts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'], name=op.f('fk_fcs_group_id_waitlist_groups'), ondelete='CASCADE')
    )
    op.create_table('fit_module',
    sa.Column('fit_id', sa.Integer(), nullable=False),
    sa.Column('module_id', sa.Integer(), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['fit_id'], ['fittings.id'], name=op.f('fk_fit_module_fit_id_fittings')),
    sa.ForeignKeyConstraint(['module_id'], ['invtypes.type_id'], name=op.f('fk_fit_module_module_id_invtypes')),
    sa.PrimaryKeyConstraint('fit_id', 'module_id', name=op.f('pk_fit_module'))
    )
    op.create_table('fleetmanager',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_fleetmanager_account_id_accounts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'], name=op.f('fk_fleetmanager_group_id_waitlist_groups'), ondelete='CASCADE')
    )
    op.create_table('linked_chars',
    sa.Column('id', sa.Integer(), nullable=True),
    sa.Column('char_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['char_id'], ['characters.id'], name=op.f('fk_linked_chars_char_id_characters'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['id'], ['accounts.id'], name=op.f('fk_linked_chars_id_accounts'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('ssotoken',
    sa.Column('account_id', sa.Integer(), nullable=False),
    sa.Column('refresh_token', sa.String(length=128), nullable=True),
    sa.Column('access_token', sa.String(length=128), nullable=True),
    sa.Column('access_token_expires', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_ssotoken_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('account_id', name=op.f('pk_ssotoken'))
    )
    op.create_table('trivia',
    sa.Column('trivia_id', sa.Integer(), nullable=False),
    sa.Column('created_by_id', sa.Integer(), nullable=True),
    sa.Column('description', sa.String(length=5000), nullable=True),
    sa.Column('alert_text', sa.String(length=1000), nullable=True),
    sa.Column('from_time', sa.DateTime(), nullable=True),
    sa.Column('to_time', sa.DateTime(), nullable=True),
    sa.CheckConstraint('to_time > from_time', name=op.f('ck_trivia_to_bigger_from')),
    sa.ForeignKeyConstraint(['created_by_id'], ['accounts.id'], name=op.f('fk_trivia_created_by_id_accounts')),
    sa.PrimaryKeyConstraint('trivia_id', name=op.f('pk_trivia'))
    )
    op.create_table('waitlists',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=True),
    sa.Column('waitlist_type', sa.String(length=20), nullable=True),
    sa.Column('group_id', sa.Integer(), nullable=True),
    sa.Column('display_title', sa.String(length=100), nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'], name=op.f('fk_waitlists_group_id_waitlist_groups')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_waitlists')),
    sa.UniqueConstraint('group_id', 'waitlist_type', name='uq_waitlists_group_id_waitlist_type')
    )
    op.create_table('calendar_backseat',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_calendar_backseat_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_id'], ['calendar_event.event_id'], name=op.f('fk_calendar_backseat_event_id_calendar_event'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('calendar_organizer',
    sa.Column('account_id', sa.Integer(), nullable=True),
    sa.Column('event_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_calendar_organizer_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_id'], ['calendar_event.event_id'], name=op.f('fk_calendar_organizer_event_id_calendar_event'), onupdate='CASCADE', ondelete='CASCADE')
    )
    op.create_table('comp_history_ext_inv',
    sa.Column('invite_ext_id', sa.Integer(), nullable=False),
    sa.Column('history_id', sa.Integer(), nullable=True),
    sa.Column('waitlist_id', sa.Integer(), nullable=True),
    sa.Column('time_created', sa.DateTime(), nullable=True),
    sa.Column('time_invited', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['history_id'], ['comp_history.history_id'], name=op.f('fk_comp_history_ext_inv_history_id_comp_history')),
    sa.ForeignKeyConstraint(['waitlist_id'], ['waitlists.id'], name=op.f('fk_comp_history_ext_inv_waitlist_id_waitlists')),
    sa.PrimaryKeyConstraint('invite_ext_id', name=op.f('pk_comp_history_ext_inv'))
    )
    op.create_table('comp_history_fits',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('history_id', sa.Integer(), nullable=True),
    sa.Column('fit_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['fit_id'], ['fittings.id'], name=op.f('fk_comp_history_fits_fit_id_fittings')),
    sa.ForeignKeyConstraint(['history_id'], ['comp_history.history_id'], name=op.f('fk_comp_history_fits_history_id_comp_history')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_comp_history_fits'))
    )
    op.create_table('role_changes',
    sa.Column('role_change_id', sa.Integer(), nullable=False),
    sa.Column('entry_id', sa.Integer(), nullable=False),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('added', sa.Boolean(name='added'), nullable=False),
    sa.ForeignKeyConstraint(['entry_id'], ['account_notes.entry_id'], name=op.f('fk_role_changes_entry_id_account_notes'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_role_changes_role_id_roles'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_change_id', name=op.f('pk_role_changes'))
    )
    op.create_table('tokenscope',
    sa.Column('token_id', sa.Integer(), nullable=False),
    sa.Column('scope_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['scope_id'], ['eveapiscope.scope_id'], name=op.f('fk_tokenscope_scope_id_eveapiscope'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['token_id'], ['ssotoken.account_id'], name=op.f('fk_tokenscope_token_id_ssotoken'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('token_id', 'scope_id', name=op.f('pk_tokenscope'))
    )
    op.create_table('trivia_question',
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('trivia_id', sa.Integer(), nullable=True),
    sa.Column('question_text', sa.String(length=1000), nullable=True),
    sa.Column('answer_type', sa.String(length=255), nullable=True),
    sa.Column('answer_connection', sa.Enum('AND', 'OR', 'NOT', 'NONE', name='answer_connection'), nullable=True),
    sa.Column('input_placeholder', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['trivia_id'], ['trivia.trivia_id'], name=op.f('fk_trivia_question_trivia_id_trivia')),
    sa.PrimaryKeyConstraint('question_id', name=op.f('pk_trivia_question'))
    )
    op.create_table('trivia_submission',
    sa.Column('submission_id', sa.Integer(), nullable=False),
    sa.Column('trivia_id', sa.Integer(), nullable=True),
    sa.Column('submittor_id', sa.Integer(), nullable=True),
    sa.Column('submittor_account_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['submittor_account_id'], ['accounts.id'], name=op.f('fk_trivia_submission_submittor_account_id_accounts')),
    sa.ForeignKeyConstraint(['submittor_id'], ['characters.id'], name=op.f('fk_trivia_submission_submittor_id_characters')),
    sa.ForeignKeyConstraint(['trivia_id'], ['trivia.trivia_id'], name=op.f('fk_trivia_submission_trivia_id_trivia')),
    sa.PrimaryKeyConstraint('submission_id', name=op.f('pk_trivia_submission'))
    )
    op.create_table('waitlist_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('creation', sa.DateTime(), nullable=True),
    sa.Column('user', sa.Integer(), nullable=True),
    sa.Column('waitlist_id', sa.Integer(), nullable=True),
    sa.Column('time_invited', sa.DateTime(), nullable=True),
    sa.Column('invite_count', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user'], ['characters.id'], name=op.f('fk_waitlist_entries_user_characters')),
    sa.ForeignKeyConstraint(['waitlist_id'], ['waitlists.id'], name=op.f('fk_waitlist_entries_waitlist_id_waitlists'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_waitlist_entries'))
    )
    op.create_table('trivia_answer',
    sa.Column('answer_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('answer_text', sa.String(length=1000), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['trivia_question.question_id'], name=op.f('fk_trivia_answer_question_id_trivia_question')),
    sa.PrimaryKeyConstraint('answer_id', 'question_id', name=op.f('pk_trivia_answer'))
    )
    op.create_table('trivia_submission_answer',
    sa.Column('submission_id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('answer_text', sa.String(length=5000), nullable=True),
    sa.ForeignKeyConstraint(['question_id'], ['trivia_question.question_id'], name=op.f('fk_trivia_submission_answer_question_id_trivia_question')),
    sa.ForeignKeyConstraint(['submission_id'], ['trivia_submission.submission_id'], name=op.f('fk_trivia_submission_answer_submission_id_trivia_submission')),
    sa.PrimaryKeyConstraint('submission_id', 'question_id', name=op.f('pk_trivia_submission_answer'))
    )
    op.create_table('waitlist_entry_fits',
    sa.Column('entry_id', sa.Integer(), nullable=True),
    sa.Column('fit_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['entry_id'], ['waitlist_entries.id'], name=op.f('fk_waitlist_entry_fits_entry_id_waitlist_entries'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['fit_id'], ['fittings.id'], name=op.f('fk_waitlist_entry_fits_fit_id_fittings'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('fit_id', name=op.f('pk_waitlist_entry_fits'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('waitlist_entry_fits')
    op.drop_table('trivia_submission_answer')
    op.drop_table('trivia_answer')
    op.drop_table('waitlist_entries')
    op.drop_table('trivia_submission')
    op.drop_table('trivia_question')
    op.drop_table('tokenscope')
    op.drop_table('role_changes')
    op.drop_table('comp_history_fits')
    op.drop_table('comp_history_ext_inv')
    op.drop_table('calendar_organizer')
    op.drop_table('calendar_backseat')
    op.drop_table('waitlists')
    op.drop_table('trivia')
    op.drop_table('ssotoken')
    op.drop_table('linked_chars')
    op.drop_table('fleetmanager')
    op.drop_table('fit_module')
    op.drop_table('fcs')
    op.drop_table('event_history_info')
    op.drop_table('crest_fleets')
    op.drop_index(op.f('ix_comp_history_time'), table_name='comp_history')
    op.drop_table('comp_history')
    op.drop_table('ccvote')
    op.drop_index(op.f('ix_calendar_event_event_time'), table_name='calendar_event')
    op.drop_index(op.f('ix_calendar_event_event_creator_id'), table_name='calendar_event')
    op.drop_index(op.f('ix_calendar_event_event_category_id'), table_name='calendar_event')
    op.drop_index(op.f('ix_calendar_event_event_approved'), table_name='calendar_event')
    op.drop_table('calendar_event')
    op.drop_table('backseats')
    op.drop_table('account_roles')
    op.drop_index(op.f('ix_account_notes_time'), table_name='account_notes')
    op.drop_table('account_notes')
    op.drop_table('whitelist')
    op.drop_table('waitlist_groups')
    op.drop_index(op.f('ix_tickets_time'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_state'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_character_id'), table_name='tickets')
    op.drop_table('tickets')
    op.drop_table('permission_roles')
    op.drop_table('incursion_layout')
    op.drop_table('fittings')
    op.drop_index(op.f('ix_feedback_user'), table_name='feedback')
    op.drop_index(op.f('ix_feedback_last_changed'), table_name='feedback')
    op.drop_table('feedback')
    op.drop_index(op.f('ix_event_history_entries_time'), table_name='event_history_entries')
    op.drop_table('event_history_entries')
    op.drop_index(op.f('ix_ban_name'), table_name='ban')
    op.drop_table('ban')
    op.drop_table('accounts')
    op.drop_table('ts_dati')
    op.drop_index(op.f('ix_station_station_name'), table_name='station')
    op.drop_table('station')
    op.drop_index(op.f('ix_solarsystem_solar_system_name'), table_name='solarsystem')
    op.drop_table('solarsystem')
    op.drop_table('settings')
    op.drop_table('roles')
    op.drop_table('permissions')
    op.drop_index(op.f('ix_invtypes_group_id'), table_name='invtypes')
    op.drop_table('invtypes')
    op.drop_table('invmarketgroups')
    op.drop_table('event_history_types')
    op.drop_index(op.f('ix_eveapiscope_scope_name'), table_name='eveapiscope')
    op.drop_table('eveapiscope')
    op.drop_index(op.f('ix_constellation_constellation_name'), table_name='constellation')
    op.drop_table('constellation')
    op.drop_table('characters')
    op.drop_index(op.f('ix_calendar_category_category_name'), table_name='calendar_category')
    op.drop_table('calendar_category')
    op.drop_index(op.f('ix_apicache_corporationinfo_name'), table_name='apicache_corporationinfo')
    op.drop_index(op.f('ix_apicache_corporationinfo_alliance_id'), table_name='apicache_corporationinfo')
    op.drop_table('apicache_corporationinfo')
    op.drop_index(op.f('ix_apicache_characterinfo_corporation_id'), table_name='apicache_characterinfo')
    op.drop_table('apicache_characterinfo')
    op.drop_index(op.f('ix_apicache_characteraffiliation_name'), table_name='apicache_characteraffiliation')
    op.drop_index(op.f('ix_apicache_characteraffiliation_corporation_name'), table_name='apicache_characteraffiliation')
    op.drop_index(op.f('ix_apicache_characteraffiliation_corporation_id'), table_name='apicache_characteraffiliation')
    op.drop_index(op.f('ix_apicache_characteraffiliation_alliance_name'), table_name='apicache_characteraffiliation')
    op.drop_index(op.f('ix_apicache_characteraffiliation_alliance_id'), table_name='apicache_characteraffiliation')
    op.drop_table('apicache_characteraffiliation')
    op.drop_index(op.f('ix_apicache_allianceinfo_executor_corp_id'), table_name='apicache_allianceinfo')
    op.drop_index(op.f('ix_apicache_allianceinfo_alliance_name'), table_name='apicache_allianceinfo')
    op.drop_table('apicache_allianceinfo')
    # ### end Alembic commands ###
