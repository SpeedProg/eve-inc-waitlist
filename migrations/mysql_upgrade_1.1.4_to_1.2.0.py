"""
This script is for updating datbases of v1.1.4
to v1.2.0.
This script is only meant for MySQL and MariaDB databases.
In this version the constraints and indexes have fixed names.
Also all column name are now lower case
This is to make sure migration scripts work between different databases.
"""
import datetime
import re
from typing import List, Union

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text, Column, String
from sqlalchemy.engine import ResultProxy, RowProxy
from alembic import op

from waitlist import db

#modify these values
database_name = "waitlist"
#don't modify any other values

alembic_version = '23de9b7d3697'

sql_get_column_names: text = text("""
    SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, IS_NULLABLE, EXTRA
    FROM
    INFORMATION_SCHEMA.COLUMNS
    WHERE
            TABLE_SCHEMA = :dbname
        AND
            TABLE_NAME = :tablename;
""")

mysql_rename_column: str = """
    ALTER TABLE %s CHANGE `%s` `%s` %s;
"""

mysql_show_index: str = """
SHOW INDEX FROM `%s`;
"""

mysql_drop_index: str = """
ALTER TABLE  `%s` DROP INDEX  `%s`;
"""

mysql_show_fk: str = """
SELECT * FROM information_schema.TABLE_CONSTRAINTS 
WHERE information_schema.TABLE_CONSTRAINTS.CONSTRAINT_TYPE = 'FOREIGN KEY' 
AND information_schema.TABLE_CONSTRAINTS.TABLE_SCHEMA = '%s'
AND information_schema.TABLE_CONSTRAINTS.TABLE_NAME = '%s';
"""

mysql_drop_fk: str = """
ALTER TABLE `%s` DROP FOREIGN KEY `%s`;
"""

mariadb_show_check: str = """
SELECT * FROM information_schema.TABLE_CONSTRAINTS 
WHERE information_schema.TABLE_CONSTRAINTS.CONSTRAINT_TYPE = 'CHECK' 
AND information_schema.TABLE_CONSTRAINTS.TABLE_SCHEMA = '%s'
AND information_schema.TABLE_CONSTRAINTS.TABLE_NAME = '%s';
"""

mariadb_drop_check: str = """
ALTER TABLE `%s` DROP CONSTRAINT `%s`;
"""

table_names: List[str] = ['account_notes', 'account_roles', 'accounts', 'alembic_version', 'apicache_allianceinfo',
                          'apicache_characteraffiliation', 'apicache_characterinfo', 'apicache_corporationinfo',
                          'backseats', 'ban', 'calendar_backseat', 'calendar_category', 'calendar_event',
                          'calendar_organizer', 'ccvote', 'characters', 'comp_history', 'comp_history_ext_inv',
                          'comp_history_fits', 'constellation', 'crest_fleets', 'eveapiscope', 'event_history_entries',
                          'event_history_info', 'event_history_types', 'fcs', 'feedback', 'fit_module', 'fittings',
                          'fleetmanager', 'incursion_layout', 'invmarketgroups', 'invtypes', 'linked_chars',
                          'permission_roles', 'permissions', 'role_changes', 'roles', 'settings', 'solarsystem',
                          'ssotoken', 'station', 'tickets', 'tokenscope', 'trivia', 'trivia_answer', 'trivia_question',
                          'trivia_submission', 'trivia_submission_answer', 'ts_dati', 'waitlist_entries',
                          'waitlist_entry_fits', 'waitlist_groups', 'waitlists', 'whitelist']

addTo = None
doFk = False


def get_type(column_info: RowProxy):
    extra_info: Union[None, str] = ''
    data_type = column_info['COLUMN_TYPE']
    is_auto_increment = False
    """
    if colum_info['CHARACTER_MAXIMUM_LENGTH'] is not None:
        extra_info = '('+str(colum_info['CHARACTER_MAXIMUM_LENGTH'])+')'
    elif colum_info['NUMERIC_PRECISION'] is not None:
        extra_info = '(' + str(colum_info['NUMERIC_PRECISION']) + ')'
    """
    if (column_info['IS_NULLABLE'] == "NO"):
        extra_info += ' NOT NULL'
    if column_info['EXTRA'] is not None and 'auto_increment' in column_info['EXTRA']:
        is_auto_increment = True
    return (data_type + ('' if extra_info is None else extra_info )), is_auto_increment


re_id = re.compile(r'(?!^|_)id$', re.IGNORECASE)

translation_table = {
    'newbro': 'new_bro',
    'odering': 'ordering'
}

def get_new_column_name(oldname: str):
    if oldname in translation_table:
        return translation_table[oldname]

    _origName = oldname
    oldname = re.sub(re_id, '_id', oldname)
    oldname = convert_case(oldname)
    #print(f"Changed {_origName} => {oldname}")
    return oldname


def upgrade():
    global addTo
    global doFk

    print('Exception no missing primary keys that we try to drop are expected to happen, please ignore')
    with db.engine.connect() as con:
        # lets see if this is a mariadb that supports check
        check_supported = supports_check(con)

        print('Dropping all Foreign Keys...')
        for table_name in table_names:
            # drop foreign keys
            try:
                fk_dbinfos: ResultProxy = con.execute(mysql_show_fk % (database_name, table_name))
                for fk_dbinfo in fk_dbinfos:
                    key_name = fk_dbinfo['CONSTRAINT_NAME']
                    statement = mysql_drop_fk % (table_name, key_name)
                    #print(f'Executing: {statement.strip()}')
                    con.execute(statement)
            except Exception as e:
                print(e)

        print('Dropping all Foreign Keys Done')


        # drop checks
        # mysql (as of now) ignores check as well as mariadb < 10.2.1
        if check_supported:
            print('Dropping Check Constraints...')
            for table_name in table_names:
                # drop foreign keys
                try:
                    ck_dbinfos: ResultProxy = con.execute(mariadb_show_check % (database_name, table_name))
                    for ck_dbinfo in ck_dbinfos:
                        key_name = ck_dbinfo['CONSTRAINT_NAME']
                        statement = mariadb_drop_check % (table_name, key_name)
                        #print(f'Executing: {statement.strip()}')
                        con.execute(statement)
                except Exception as e:
                    print(e)

            print('Dropping Check Constraints Done')


        # rename all the columns
        # this also removes auto increment :)
        print('Renaming Columns...')
        tables_with_auto_increment = []
        for table_name in table_names:
            columns_with_auto_increment = []
            table_columns: ResultProxy = db.engine.execute(sql_get_column_names,
                                                           dbname=database_name, tablename=table_name)
            columns: List[List[str, str]] = []
            for column_info in table_columns:
                type, auto_increment = get_type(column_info)
                if auto_increment:
                    columns_with_auto_increment.append([column_info['COLUMN_NAME'], type + " AUTO_INCREMENT"])

                columns.append([column_info['COLUMN_NAME'], type])
            table_columns.close()

            for column_info in columns:
                new_column_name = get_new_column_name(column_info[0])
                mysql_alter = mysql_rename_column % (table_name, column_info[0], new_column_name, column_info[1])
                #print(f'Executing: {mysql_alter.strip()}')
                con.execute(mysql_alter)

            if len(columns_with_auto_increment) > 0:
                tables_with_auto_increment.append([table_name, columns_with_auto_increment])

        print("Renaming Columns Done")

        # now that auto_increment is gone, we can drop all indexes

        # drop all the primary keys
        print('Dropping Primary Keys...')
        mysql_drop_pk: str = """
        ALTER TABLE `%s` DROP PRIMARY KEY;
        """
        for table_name in table_names:
            # there might be lots of exceptions where when no primary key exists, just ignore
            try:
                statement = mysql_drop_pk % (table_name,)
                #print(f'Executing: {statement.strip()}')
                con.execute(statement)
            except Exception as e:
                print(e)

        print('Dropping Primary Keys Done')

        # drop indices
        print('Dropping Indices..')
        for table_name in table_names:

            index_dbinfos: ResultProxy = con.execute(mysql_show_index % table_name)
            # for some reason PRIMARY is in there multiple times, sometimes
            removed_index: set = set()
            for index_dbinfo in index_dbinfos:
                try:
                    index_name = index_dbinfo['Key_name']
                    if index_name in removed_index:
                        continue
                    statement = mysql_drop_index % (table_name, index_name)
                    #print(f'Executing: {statement.strip()}')
                    con.execute(statement)
                    removed_index.add(index_name)
                except Exception as e:
                    print(e)

        print('Dropping Indices Done')


        # create contexts for alembic
        mig_context = MigrationContext.configure(connection=con, dialect_name='mysql',
                                                 opts={'target_metadata': db.metadata})


        with Operations.context(mig_context):
            doFk = False
            print('Creating Primary Keys and Indices and Checks...')
            add_keys_and_constraits()
            print('Creating Primary Keys and Indices and Checks Done')

            # lets add the new column first
            print('Adding new colum to waitlists table...')
            with op.batch_alter_table('waitlists') as batch:
                batch.add_column(Column('waitlist_type', String(20)))

            print('Adding new colum to waitlists table Done')

            # now get waitlist groups
            mysql_get_wl_groups: str = """
            SELECT xupwl_id, logiwl_id, dpswl_id, sniperwl_id, otherwl_id
            FROM `%s`;
            """
            groups_result: ResultProxy = con.execute(mysql_get_wl_groups % ('waitlist_groups'))

            mysql_set_wl_type: str = """
            UPDATE `waitlists`
            SET waitlist_type = '%s'
            WHERE id = %s;
            """

            print('Setting new waitlists column from old references...')
            for group_info in groups_result:
                for name in ['xupwl_id', 'logiwl_id', 'dpswl_id', 'sniperwl_id', 'otherwl_id']:
                    if group_info[name] is not None:
                        # we got the id here
                        statement = mysql_set_wl_type % (name.replace('wl_id', ''), group_info[name])
                        #print(statement)
                        con.execute(statement)

            # now all the waitlists should know their type
            print('Setting new waitlists column from old references Done')

            # we can remove the columns 'xupwl_id', 'logiwl_id', 'dpswl_id', 'sniperwl_id', 'otherwl_id' now
            print('Removing old reference columns from waitlist_groups tables...')
            with op.batch_alter_table('waitlist_groups') as batch:
                for column_name in ['xupwl_id', 'logiwl_id', 'dpswl_id', 'sniperwl_id', 'otherwl_id']:
                    batch.drop_column(column_name)

            print('Removing old reference columns from waitlist_groups tables Done')

            # UniqueConstraint('group_id', 'waitlist_type')
            print('Adding Unique constraint for new waitlists column...')
            with op.batch_alter_table('waitlists') as batch:
                batch.create_unique_constraint(constraint_name='uq_waitlists_group_id_waitlist_type', columns=['group_id', 'waitlist_type'])

            print('Adding Unique constraint for new waitlists column Done')

            # lets readd autoincrement columns
            print('Readding AUTO_INCREMENT to columns where it got removed earlier...')
            for table_data in tables_with_auto_increment:
                table_name = table_data[0]

                for column_info in table_data[1]:
                    new_column_name = get_new_column_name(column_info[0])
                    print(f'Working on Table {table_name}.{new_column_name}')
                    mysql_alter = mysql_rename_column % (table_name, new_column_name, new_column_name, column_info[1])
                    #print(mysql_alter)
                    con.execute(mysql_alter)
            print('Readding AUTO_INCREMENT to columns where it got removed earlier... Done')

            doFk = True
            print('Readding Foreign Keys...')
            add_keys_and_constraits()
            print("Readding Foreign Keys Done")

            # now that we are done, set the alembic version
            print('Setting Alembic version')
            mysql_set_alembic_version: str = """
            DELETE FROM alembic_version;
            INSERT INTO alembic_version VALUES ('%s');
            """
            con.execute(mysql_set_alembic_version % (alembic_version,))

            print(f"Changed alembic_version to {alembic_version}")


def supports_check(con) -> bool:
    result: ResultProxy = con.execute('SELECT VERSION();')
    if result.rowcount != 1:
        return False

    first_row: RowProxy = result.first()
    version_string: str = first_row['VERSION()']
    # MariaDB supports this since 10.2.1
    # other version (mysql too) just ignore it, so we can't check to see if it errors
    if 'MariaDB' in version_string:
        version_string = version_string.replace('-MariaDB', '')
        nums = version_string.split('.')
        if len(nums) < 3:
            return False

        if int(nums[0]) > 10:
            return True

        if int(nums[0]) == 10:
            if int(nums[1]) > 2:
                return True
            if int(nums[1]) == 2:
                if int(nums[2]) >= 1:
                    return True

    return False




def create_index(name, table_name, column_name, unique=False):
    if not doFk:
        addTo.create_index(name, column_name, unique=unique)


def UniqueConstraint(column, name=None):
    if not doFk:
        addTo.create_unique_constraint(constraint_name=name, columns=[column])


def PrimaryKeyConstraint(*columns, name=None):
    if not doFk:
        addTo.create_primary_key(name, columns)


def ForeignKeyConstraint(own_columns: List[str], other_ids: List[str], name=None, onupdate=None, ondelete=None):
    if doFk:
        split_targetid= other_ids[0].split('.')
        target_table = split_targetid[0]
        target_column = split_targetid[1]
        addTo.create_foreign_key(name, target_table, own_columns, [target_column], onupdate=onupdate, ondelete=ondelete)



def add_keys_and_constraits():
    global  addTo
    with op.batch_alter_table('account_notes') as batch:
        addTo = batch
        if doFk:
            batch.create_foreign_key(op.f('fk_account_notes_account_id_accounts'),
                                     'accounts',
                                     ['account_id'], ['id'])
            batch.create_foreign_key(op.f('fk_account_notes_by_account_id_accounts'),
                                     'accounts',
                                     ['by_account_id'], ['id'])
        else:
            PrimaryKeyConstraint('entry_id', name=op.f('pk_account_notes'))
            batch.create_index(op.f('ix_account_notes_time'), ['time'], unique=False)

    with op.batch_alter_table('account_roles') as batch:
        addTo = batch
        if doFk:
            batch.create_foreign_key(op.f('fk_account_roles_account_id_accounts'),
                                     'accounts',
                                     ['account_id'], ['id'],
                                     onupdate='CASCADE', ondelete='CASCADE')
            batch.create_foreign_key(op.f('fk_account_roles_role_id_roles'),
                                     'roles',
                                     ['role_id'], ['id'],
                                     onupdate='CASCADE', ondelete='CASCADE')

    with op.batch_alter_table('accounts') as batch:
        addTo = batch
        ForeignKeyConstraint(['current_char'], ['characters.id'],
                             name=op.f('fk_accounts_current_char_characters'))
        PrimaryKeyConstraint('id', name=op.f('pk_accounts'))
        UniqueConstraint('login_token', name=op.f('uq_accounts_login_token'))
        UniqueConstraint('username', name=op.f('uq_accounts_username'))

    with op.batch_alter_table('apicache_allianceinfo') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_apicache_allianceinfo'))
        if not doFk:
            batch.create_index(op.f('ix_apicache_allianceinfo_alliance_name'), ['alliance_name'],
                               unique=False)
            batch.create_index(op.f('ix_apicache_allianceinfo_executor_corp_id'),
                               ['executor_corp_id'], unique=False)

    with op.batch_alter_table('apicache_characteraffiliation') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_apicache_characteraffiliation'))
        create_index(op.f('ix_apicache_characteraffiliation_alliance_id'), 'apicache_characteraffiliation',
                     ['alliance_id'], unique=False)
        create_index(op.f('ix_apicache_characteraffiliation_alliance_name'), 'apicache_characteraffiliation',
                     ['alliance_name'], unique=False)
        create_index(op.f('ix_apicache_characteraffiliation_corporation_id'), 'apicache_characteraffiliation',
                     ['corporation_id'], unique=False)
        create_index(op.f('ix_apicache_characteraffiliation_corporation_name'), 'apicache_characteraffiliation',
                     ['corporation_name'], unique=False)
        create_index(op.f('ix_apicache_characteraffiliation_name'), 'apicache_characteraffiliation', ['name'],
                     unique=False)

    with op.batch_alter_table('apicache_characterinfo') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_apicache_characterinfo'))
        create_index(op.f('ix_apicache_characterinfo_corporation_id'), 'apicache_characterinfo',
                     ['corporation_id'], unique=False)

    with op.batch_alter_table('apicache_corporationinfo') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_apicache_corporationinfo'))
        create_index(op.f('ix_apicache_corporationinfo_alliance_id'), 'apicache_corporationinfo',
                     ['alliance_id'], unique=False)
        create_index(op.f('ix_apicache_corporationinfo_name'), 'apicache_corporationinfo', ['name'],
                     unique=False)

    with op.batch_alter_table('backseats') as batch:
        addTo = batch
        ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_backseats_account_id_accounts'),
                             ondelete='CASCADE'),
        ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'],
                             name=op.f('fk_backseats_group_id_waitlist_groups'), ondelete='CASCADE')

    with op.batch_alter_table('ban') as batch:
        addTo = batch
        ForeignKeyConstraint(['admin'], ['characters.id'], name=op.f('fk_ban_admin_characters')),
        PrimaryKeyConstraint('id', name=op.f('pk_ban'))
        create_index(op.f('ix_ban_name'), 'ban', ['name'], unique=False)

    with op.batch_alter_table('calendar_backseat') as batch:
        addTo = batch
        ForeignKeyConstraint(['account_id'], ['accounts.id'],
                             name=op.f('fk_calendar_backseat_account_id_accounts'), onupdate='CASCADE',
                             ondelete='CASCADE'),
        ForeignKeyConstraint(['event_id'], ['calendar_event.event_id'],
                             name=op.f('fk_calendar_backseat_event_id_calendar_event'), onupdate='CASCADE',
                             ondelete='CASCADE')

    with op.batch_alter_table('calendar_category') as batch:
        addTo = batch
        PrimaryKeyConstraint('category_id', name=op.f('pk_calendar_category'))
        create_index(op.f('ix_calendar_category_category_name'), 'calendar_category', ['category_name'],
                     unique=False)

    with op.batch_alter_table('calendar_event') as batch:
        addTo = batch
        ForeignKeyConstraint(['approver_id'], ['accounts.id'], name=op.f('fk_calendar_event_approver_id_accounts'),
                             onupdate='CASCADE', ondelete='CASCADE')
        ForeignKeyConstraint(['event_category_id'], ['calendar_category.category_id'],
                             name=op.f('fk_calendar_event_event_category_id_calendar_category'), onupdate='CASCADE',
                             ondelete='CASCADE')
        ForeignKeyConstraint(['event_creator_id'], ['accounts.id'],
                             name=op.f('fk_calendar_event_event_creator_id_accounts'), onupdate='CASCADE',
                             ondelete='CASCADE')
        PrimaryKeyConstraint('event_id', name=op.f('pk_calendar_event'))

        create_index(op.f('ix_calendar_event_event_approved'), 'calendar_event', ['event_approved'], unique=False)
        create_index(op.f('ix_calendar_event_event_category_id'), 'calendar_event', ['event_category_id'], unique=False)
        create_index(op.f('ix_calendar_event_event_creator_id'), 'calendar_event', ['event_creator_id'], unique=False)
        create_index(op.f('ix_calendar_event_event_time'), 'calendar_event', ['event_time'], unique=False)

    with op.batch_alter_table('calendar_organizer') as batch:
        addTo = batch
        ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_calendar_organizer_account_id_accounts'),
                             onupdate='CASCADE', ondelete='CASCADE')
        ForeignKeyConstraint(['event_id'], ['calendar_event.event_id'],
                             name=op.f('fk_calendar_organizer_event_id_calendar_event'), onupdate='CASCADE',
                             ondelete='CASCADE')

    with op.batch_alter_table('ccvote') as batch:
        addTo = batch
        ForeignKeyConstraint(['fcvote_id'], ['accounts.id'], name=op.f('fk_ccvote_fcvote_id_accounts'))
        ForeignKeyConstraint(['lmvote_id'], ['accounts.id'], name=op.f('fk_ccvote_lmvote_id_accounts'))
        ForeignKeyConstraint(['voter_id'], ['characters.id'], name=op.f('fk_ccvote_voter_id_characters'))
        PrimaryKeyConstraint('ccvote_id', name=op.f('pk_ccvote'))

    with op.batch_alter_table('characters') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_characters'))

    with op.batch_alter_table('comp_history') as batch:
        addTo = batch
        ForeignKeyConstraint(['source_id'], ['accounts.id'], name=op.f('fk_comp_history_source_id_accounts'))
        ForeignKeyConstraint(['target_id'], ['characters.id'], name=op.f('fk_comp_history_target_id_characters'))
        PrimaryKeyConstraint('history_id', name=op.f('pk_comp_history'))
        create_index(op.f('ix_comp_history_time'), 'comp_history', ['time'], unique=False)

    with op.batch_alter_table('comp_history_ext_inv') as batch:
        addTo = batch
        ForeignKeyConstraint(['history_id'], ['comp_history.history_id'],
                             name=op.f('fk_comp_history_ext_inv_history_id_comp_history'))
        ForeignKeyConstraint(['waitlist_id'], ['waitlists.id'],
                             name=op.f('fk_comp_history_ext_inv_waitlist_id_waitlists'))
        PrimaryKeyConstraint('invite_ext_id', name=op.f('pk_comp_history_ext_inv'))

    with op.batch_alter_table('comp_history_fits') as batch:
        addTo = batch
        ForeignKeyConstraint(['fit_id'], ['fittings.id'], name=op.f('fk_comp_history_fits_fit_id_fittings'))
        ForeignKeyConstraint(['history_id'], ['comp_history.history_id'],
                             name=op.f('fk_comp_history_fits_history_id_comp_history'))
        PrimaryKeyConstraint('id', name=op.f('pk_comp_history_fits'))

    with op.batch_alter_table('constellation') as batch:
        addTo = batch
        PrimaryKeyConstraint('constellation_id', name=op.f('pk_constellation'))
        create_index(op.f('ix_constellation_constellation_name'), 'constellation', ['constellation_name'],
                     unique=True)

    with op.batch_alter_table('crest_fleets') as batch:
        addTo = batch
        ForeignKeyConstraint(['comp_id'], ['accounts.id'], name=op.f('fk_crest_fleets_comp_id_accounts'))
        ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'],
                             name=op.f('fk_crest_fleets_group_id_waitlist_groups'))
        PrimaryKeyConstraint('fleet_id', name=op.f('pk_crest_fleets'))

    with op.batch_alter_table('eveapiscope') as batch:
        addTo = batch
        PrimaryKeyConstraint('scope_id', name=op.f('pk_eveapiscope'))
        create_index(op.f('ix_eveapiscope_scope_name'), 'eveapiscope', ['scope_name'], unique=False)

    with op.batch_alter_table('event_history_entries') as batch:
        addTo = batch
        ForeignKeyConstraint(['type_id'], ['event_history_types.type_id'],
                             name=op.f('fk_event_history_entries_type_id_event_history_types'))
        PrimaryKeyConstraint('history_id', name=op.f('pk_event_history_entries'))
        create_index(op.f('ix_event_history_entries_time'), 'event_history_entries', ['time'], unique=False)

    with op.batch_alter_table('event_history_info') as batch:
        addTo = batch
        ForeignKeyConstraint(['history_id'], ['event_history_entries.history_id'],
                             name=op.f('fk_event_history_info_history_id_event_history_entries'))
        PrimaryKeyConstraint('info_id', name=op.f('pk_event_history_info'))

    with op.batch_alter_table('event_history_types') as batch:
        addTo = batch
        PrimaryKeyConstraint('type_id', name=op.f('pk_event_history_types'))
        UniqueConstraint('type_name', name=op.f('uq_event_history_types_type_name'))

    with op.batch_alter_table('fcs') as batch:
        addTo = batch
        ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_fcs_account_id_accounts'),
                             ondelete='CASCADE')
        ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'],
                             name=op.f('fk_fcs_group_id_waitlist_groups'), ondelete='CASCADE')

    with op.batch_alter_table('feedback') as batch:
        addTo = batch
        ForeignKeyConstraint(['user'], ['characters.id'], name=op.f('fk_feedback_user_characters'))
        PrimaryKeyConstraint('id', name=op.f('pk_feedback'))
        create_index(op.f('ix_feedback_last_changed'), 'feedback', ['last_changed'], unique=False)
        create_index(op.f('ix_feedback_user'), 'feedback', ['user'], unique=True)

    with op.batch_alter_table('fit_module') as batch:
        addTo = batch
        ForeignKeyConstraint(['fit_id'], ['fittings.id'], name=op.f('fk_fit_module_fit_id_fittings'))
        ForeignKeyConstraint(['module_id'], ['invtypes.type_id'], name=op.f('fk_fit_module_module_id_invtypes'))
        PrimaryKeyConstraint('fit_id', 'module_id', name=op.f('pk_fit_module'))

    with op.batch_alter_table('fittings') as batch:
        addTo = batch
        ForeignKeyConstraint(['ship_type'], ['invtypes.type_id'], name=op.f('fk_fittings_ship_type_invtypes'))
        PrimaryKeyConstraint('id', name=op.f('pk_fittings'))

    with op.batch_alter_table('fleetmanager') as batch:
        addTo = batch
        ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_fleetmanager_account_id_accounts'),
                             ondelete='CASCADE')
        ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'],
                             name=op.f('fk_fleetmanager_group_id_waitlist_groups'), ondelete='CASCADE')

    with op.batch_alter_table('incursion_layout') as batch:
        addTo = batch
        ForeignKeyConstraint(['constellation'], ['constellation.constellation_id'],
                             name=op.f('fk_incursion_layout_constellation_constellation'))
        ForeignKeyConstraint(['dockup'], ['station.station_id'],
                             name=op.f('fk_incursion_layout_dockup_station'))
        ForeignKeyConstraint(['headquarter'], ['solarsystem.solar_system_id'],
                             name=op.f('fk_incursion_layout_headquarter_solarsystem'))
        ForeignKeyConstraint(['staging'], ['solarsystem.solar_system_id'],
                             name=op.f('fk_incursion_layout_staging_solarsystem'))
        PrimaryKeyConstraint('constellation', name=op.f('pk_incursion_layout'))

    with op.batch_alter_table('invmarketgroups') as batch:
        addTo = batch
        ForeignKeyConstraint(['parent_group_id'], ['invmarketgroups.market_group_id'],
                             name=op.f('fk_invmarketgroups_parent_group_id_invmarketgroups'))
        PrimaryKeyConstraint('market_group_id', name=op.f('pk_invmarketgroups'))

    with op.batch_alter_table('invtypes') as batch:
        addTo = batch
        PrimaryKeyConstraint('type_id', name=op.f('pk_invtypes'))
        create_index(op.f('ix_invtypes_group_id'), 'invtypes', ['group_id'], unique=False)

    with op.batch_alter_table('linked_chars') as batch:
        addTo = batch
        ForeignKeyConstraint(['char_id'], ['characters.id'], name=op.f('fk_linked_chars_char_id_characters'),
                             onupdate='CASCADE', ondelete='CASCADE')
        ForeignKeyConstraint(['id'], ['accounts.id'], name=op.f('fk_linked_chars_id_accounts'),
                             onupdate='CASCADE', ondelete='CASCADE')

    with op.batch_alter_table('permission_roles') as batch:
        addTo = batch
        ForeignKeyConstraint(['permission'], ['permissions.id'],
                             name=op.f('fk_permission_roles_permission_permissions'))
        ForeignKeyConstraint(['role'], ['roles.id'], name=op.f('fk_permission_roles_role_roles'))

    with op.batch_alter_table('permissions') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_permissions'))
        UniqueConstraint('name', name=op.f('uq_permissions_name'))

    with op.batch_alter_table('role_changes') as batch:
        addTo = batch
        ForeignKeyConstraint(['entry_id'], ['account_notes.entry_id'],
                             name=op.f('fk_role_changes_entry_id_account_notes'), onupdate='CASCADE',
                             ondelete='CASCADE')
        ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_role_changes_role_id_roles'),
                             onupdate='CASCADE', ondelete='CASCADE')
        PrimaryKeyConstraint('role_change_id', name=op.f('pk_role_changes'))

    with op.batch_alter_table('roles') as batch:
        addTo = batch
        PrimaryKeyConstraint('id', name=op.f('pk_roles'))
        UniqueConstraint('name', name=op.f('uq_roles_name'))

    with op.batch_alter_table('settings') as batch:
        addTo = batch
        PrimaryKeyConstraint('key', name=op.f('pk_settings'))

    with op.batch_alter_table('solarsystem') as batch:
        addTo = batch
        PrimaryKeyConstraint('solar_system_id', name=op.f('pk_solarsystem'))
        create_index(op.f('ix_solarsystem_solar_system_name'), 'solarsystem', ['solar_system_name'], unique=True)

    with op.batch_alter_table('ssotoken') as batch:
        addTo = batch
        ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_ssotoken_account_id_accounts'),
                             onupdate='CASCADE', ondelete='CASCADE')
        PrimaryKeyConstraint('account_id', name=op.f('pk_ssotoken'))

    with op.batch_alter_table('station') as batch:
        addTo = batch
        PrimaryKeyConstraint('station_id', name=op.f('pk_station'))
        create_index(op.f('ix_station_station_name'), 'station', ['station_name'], unique=True)

    with op.batch_alter_table('tickets') as batch:
        addTo = batch
        ForeignKeyConstraint(['character_id'], ['characters.id'],
                             name=op.f('fk_tickets_character_id_characters'))
        PrimaryKeyConstraint('id', name=op.f('pk_tickets'))
        create_index(op.f('ix_tickets_character_id'), 'tickets', ['character_id'], unique=False)
        create_index(op.f('ix_tickets_state'), 'tickets', ['state'], unique=False)
        create_index(op.f('ix_tickets_time'), 'tickets', ['time'], unique=False)

    with op.batch_alter_table('tokenscope') as batch:
        addTo = batch
        ForeignKeyConstraint(['scope_id'], ['eveapiscope.scope_id'],
                             name=op.f('fk_tokenscope_scope_id_eveapiscope'), onupdate='CASCADE',
                             ondelete='CASCADE')
        ForeignKeyConstraint(['token_id'], ['ssotoken.account_id'], name=op.f('fk_tokenscope_token_id_ssotoken'),
                             onupdate='CASCADE', ondelete='CASCADE')
        PrimaryKeyConstraint('token_id', 'scope_id', name=op.f('pk_tokenscope'))

    with op.batch_alter_table('trivia') as batch:
        addTo = batch
        # mysql (as of now) and mariadb < 10.2.1 ignores these
        if not doFk:
            batch.create_check_constraint(op.f('ck_trivia_to_bigger_from'), 'to_time > from_time')
        ForeignKeyConstraint(['created_by_id'], ['accounts.id'], name=op.f('fk_trivia_created_by_id_accounts'))
        PrimaryKeyConstraint('trivia_id', name=op.f('pk_trivia'))

    with op.batch_alter_table('trivia_answer') as batch:
        addTo = batch
        ForeignKeyConstraint(['question_id'], ['trivia_question.question_id'],
                             name=op.f('fk_trivia_answer_question_id_trivia_question'))
        PrimaryKeyConstraint('answer_id', 'question_id', name=op.f('pk_trivia_answer'))

    with op.batch_alter_table('trivia_question') as batch:
        addTo = batch
        ForeignKeyConstraint(['trivia_id'], ['trivia.trivia_id'],
                             name=op.f('fk_trivia_question_trivia_id_trivia'))
        PrimaryKeyConstraint('question_id', name=op.f('pk_trivia_question'))
        if not doFk:
            batch.create_check_constraint('answer_connection',
                                          "answer_connection IN ('AND', 'OR', 'NOT', 'NONE')")

    with op.batch_alter_table('trivia_submission') as batch:
        addTo = batch
        ForeignKeyConstraint(['submittor_account_id'], ['accounts.id'],
                             name=op.f('fk_trivia_submission_submittor_account_id_accounts'))
        ForeignKeyConstraint(['submittor_id'], ['characters.id'],
                             name=op.f('fk_trivia_submission_submittor_id_characters'))
        ForeignKeyConstraint(['trivia_id'], ['trivia.trivia_id'],
                             name=op.f('fk_trivia_submission_trivia_id_trivia'))
        PrimaryKeyConstraint('submission_id', name=op.f('pk_trivia_submission'))

    with op.batch_alter_table('trivia_submission_answer') as batch:
        addTo = batch
        ForeignKeyConstraint(['question_id'], ['trivia_question.question_id'],
                             name=op.f('fk_trivia_submission_answer_question_id_trivia_question'))
        ForeignKeyConstraint(['submission_id'], ['trivia_submission.submission_id'],
                             name=op.f('fk_trivia_submission_answer_submission_id_trivia_submission'))
        PrimaryKeyConstraint('submission_id', 'question_id', name=op.f('pk_trivia_submission_answer'))

    with op.batch_alter_table('ts_dati') as batch:
        addTo = batch
        PrimaryKeyConstraint('teamspeak_id', name=op.f('pk_ts_dati'))

    with op.batch_alter_table('waitlist_entries') as batch:
        addTo = batch
        ForeignKeyConstraint(['user'], ['characters.id'], name=op.f('fk_waitlist_entries_user_characters'))
        ForeignKeyConstraint(['waitlist_id'], ['waitlists.id'],
                             name=op.f('fk_waitlist_entries_waitlist_id_waitlists'), onupdate='CASCADE',
                             ondelete='CASCADE')
        PrimaryKeyConstraint('id', name=op.f('pk_waitlist_entries'))

    with op.batch_alter_table('waitlist_entry_fits') as batch:
        addTo = batch
        ForeignKeyConstraint(['entry_id'], ['waitlist_entries.id'],
                             name=op.f('fk_waitlist_entry_fits_entry_id_waitlist_entries'), onupdate='CASCADE',
                             ondelete='CASCADE')
        ForeignKeyConstraint(['fit_id'], ['fittings.id'], name=op.f('fk_waitlist_entry_fits_fit_id_fittings'),
                             onupdate='CASCADE', ondelete='CASCADE')
        PrimaryKeyConstraint('fit_id', name=op.f('pk_waitlist_entry_fits'))

    with op.batch_alter_table('waitlist_groups') as batch:
        addTo = batch
        ForeignKeyConstraint(['constellation_id'], ['constellation.constellation_id'],
                             name=op.f('fk_waitlist_groups_constellation_id_constellation'))
        ForeignKeyConstraint(['dockup_id'], ['station.station_id'],
                             name=op.f('fk_waitlist_groups_dockup_id_station'))
        # don't do these they will get removed
        """
        ForeignKeyConstraint(['dpswl_id'], ['waitlists.id'],
                                name=op.f('fk_waitlist_groups_dpswl_id_waitlists'))
        ForeignKeyConstraint(['logiwl_id'], ['waitlists.id'],
                                name=op.f('fk_waitlist_groups_logiwl_id_waitlists'))
        ForeignKeyConstraint(['otherwl_id'], ['waitlists.id'],
                                name=op.f('fk_waitlist_groups_otherwl_id_waitlists'))
        ForeignKeyConstraint(['sniperwl_id'], ['waitlists.id'],
                                name=op.f('fk_waitlist_groups_sniperwl_id_waitlists'))
        ForeignKeyConstraint(['xupwl_id'], ['waitlists.id'],
                                name=op.f('fk_waitlist_groups_xupwl_id_waitlists'))
        """
        ForeignKeyConstraint(['system_id'], ['solarsystem.solar_system_id'],
                             name=op.f('fk_waitlist_groups_system_id_solarsystem'))
        PrimaryKeyConstraint('group_id', name=op.f('pk_waitlist_groups'))
        UniqueConstraint('display_name', name=op.f('uq_waitlist_groups_display_name'))
        UniqueConstraint('group_name', name=op.f('uq_waitlist_groups_group_name'))

    with op.batch_alter_table('waitlists') as batch:
        addTo = batch
        ForeignKeyConstraint(['group_id'], ['waitlist_groups.group_id'],
                             name=op.f('fk_waitlists_group_id_waitlist_groups'))
        PrimaryKeyConstraint('id', name=op.f('pk_waitlists'))

    with op.batch_alter_table('whitelist') as batch:
        addTo = batch
        ForeignKeyConstraint(['admin_id'], ['characters.id'], name=op.f('fk_whitelist_admin_id_characters'))
        ForeignKeyConstraint(['character_id'], ['characters.id'],
                             name=op.f('fk_whitelist_character_id_characters'))
        PrimaryKeyConstraint('character_id', name=op.f('pk_whitelist'))


# helper stuff to convert to snake_case
rex1 = re.compile(r'(.)([A-Z][a-z]+)')
rex2 = re.compile('([a-z0-9])([A-Z])')


def convert_case(s):
    changed = rex1.sub(r'\1_\2', s)
    changed = rex2.sub(r'\1_\2', changed).lower()
    return changed.replace('__', '_')


if __name__ == "__main__":
    start = datetime.datetime.utcnow()
    print('Running migration...', start)
    upgrade()
    end = datetime.datetime.utcnow()
    print("Running migration Done", "Took", start-end)
