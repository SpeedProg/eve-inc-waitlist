from typing import Dict, Sequence, Tuple, Optional, List, KeysView

from flask_login import current_user
from time import sleep
import logging
from threading import Timer, Lock
from waitlist.base import db
from waitlist.storage.database import WaitlistGroup, CrestFleet, WaitlistEntry, \
    HistoryEntry, Character, TeamspeakDatum, Account, SSOToken, Waitlist
from datetime import datetime, timedelta
from waitlist.utility.history_utils import create_history_object
from flask.helpers import url_for
from waitlist.utility.settings import sget_active_ts_id, sget_motd_hq,\
    sget_motd_vg
from waitlist.data.sse import send_server_sent_event, InviteMissedSSE,\
    EntryRemovedSSE
from waitlist.utility.swagger import esi_scopes
from waitlist.utility.swagger.eve.fleet import EveFleetEndpoint
import flask
from waitlist.utility.swagger.eve import get_esi_client_for_account, ESIResponse
from waitlist.utility.swagger.eve.fleet import EveFleetMembers
from waitlist.utility.swagger.eve.fleet.models import FleetMember

logger = logging.getLogger(__name__)


class FleetMemberInfo:
    def __init__(self):
        self._cached_until: Dict[int, datetime] = {}
        self._lastmembers: Dict[int, Dict[int, FleetMember]] = {}
        self.__lock: Lock = Lock()

    def acquire(self):
        self.__lock.acquire()

    def release(self):
        self.__lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    def get_fleet_members(self, fleet_id: int, account: Account) -> Optional[Dict[int, FleetMember]]:
        fleetData = self._get_data(fleet_id, account)
        return fleetData.copy() if fleetData is not None else None

    def get_expires(self, fleet_id: int) -> datetime:
        return self._cached_until[fleet_id]

    def get_fleet_ids(self) -> KeysView:
        self._clean_old_fleets()
        return self._lastmembers.keys()

    def is_member_in_fleet(self, character_id: int) -> bool:
        for fleet_id in self._lastmembers.keys():
            db_fleet: CrestFleet = db.session.query(CrestFleet).get(fleet_id)
            members: Optional[Dict[int, FleetMember]] = self.get_fleet_members(fleet_id, db_fleet.comp)
            if members is not None and character_id in members:
                return True

        return False

    def _clean_old_fleets(self):
        tnow = datetime.utcnow()

        remove_ids: List[int] = []
        for fleet_id in self._lastmembers.keys():
            db_fleet: CrestFleet = db.session.query(CrestFleet).get(fleet_id)
            if db_fleet is None or db_fleet.comp is None:
                remove_ids.append(fleet_id)
                continue

            if fleet_id not in self._cached_until:
                continue

            if tnow - self._cached_until[fleet_id] < timedelta(minutes=5):
                continue

            token: Optional[SSOToken] = db_fleet.comp.get_a_sso_token_with_scopes(esi_scopes.fleetcomp_scopes)
            if token is None:
                return

            fleet_api = EveFleetEndpoint(token, fleet_id, get_esi_client_for_account(token))
            resp: ESIResponse = fleet_api.get_member()
            if resp.is_error():
                remove_ids.append(fleet_id)

        for fleet_id in remove_ids:
            del self._lastmembers[fleet_id]
            if fleet_id in self._cached_until:
                del self._cached_until[fleet_id]

        for fleet_id in db.session.query(CrestFleet.fleetID):
            if fleet_id[0] not in self._lastmembers:
                self._lastmembers[fleet_id[0]] = None
                self._cached_until[fleet_id[0]] = datetime.utcnow() - timedelta(1)

    @classmethod
    def _to_members_map(cls, response: EveFleetMembers) -> Dict[int, FleetMember]:
        data = {}
        logger.debug("Got MemberList from API %s", str(response))
        for member in response.fleet_members():
            data[member.character_id()] = member
        return data

    def _get_data(self, fleet_id: int, account: Account) -> Optional[Dict[int, FleetMember]]:
        token: Optional[SSOToken] = account.get_a_sso_token_with_scopes(['esi-fleets.read_fleet.v1'])
        if token is None:
            logger.warning('No valid SSOToken found for %s', account)
            return None

        fleet_api = EveFleetEndpoint(token, fleet_id, get_esi_client_for_account(token))
        utcnow = datetime.utcnow()
        if self._is_expired(fleet_id, utcnow):
            logger.debug("Member Data Expired for %d and account %s", fleet_id, account.username)
            try:
                logger.debug("%s Requesting Fleet Member", account.username)
                data: EveFleetMembers = fleet_api.get_member()
                if not data.is_error():
                    logger.debug("%s Got Fleet Members", account.username)
                    self._update_cache(fleet_id, data)
                    logger.debug("%s Successfully updated Fleet Members", account.username)
                elif data.code() == 404 or data.code() == 403:
                    logger.info("Failed to get Fleetmembers from API because access was denied code[%d] msg[%s]", data.code(), data.error())
                    return self.get_cache_data(fleet_id)
                else:
                    logger.error("Failed to get Fleetmembers from API code[%d] msg[%s]", data.code(), data.error())
                    return self.get_cache_data(fleet_id)
            except Exception as ex:
                logger.error("%s Getting Fleet Members caused: %s", account.username, ex, exc_info=True)
                return self.get_cache_data(fleet_id)
        else:
            logger.debug("Cache hit for %d and account %s", fleet_id, account.username)
        return self._lastmembers[fleet_id]

    def get_cache_data(self, fleet_id) -> Optional[Dict[int, FleetMember]]:
        if fleet_id in self._lastmembers and self._lastmembers[fleet_id] is not None:
            return self._lastmembers[fleet_id].copy()
        return None

    def _is_expired(self, fleet_id, utcnow) -> bool:
        if fleet_id not in self._cached_until:
            return True
        else:
            expires_at = self._cached_until[fleet_id]
            if utcnow < expires_at:
                return False
            else:
                return True

    def _update_cache(self, fleet_id: int, response: EveFleetMembers) -> None:
        self._lastmembers[fleet_id] = self._to_members_map(response)
        self._cached_until[fleet_id] = response.expires()


member_info = FleetMemberInfo()


def setup(token: SSOToken, fleet_id: int, fleet_type: str, waitlistGroup: WaitlistGroup)\
        -> None:
    fleet_api = EveFleetEndpoint(token, fleet_id)
    fleet_settings = fleet_api.get_fleet_settings()
    if fleet_settings.is_error():
        logger.error("Failed to get Fleet Settings code[%d] msg[%s]",
                     fleet_settings.code(), fleet_settings.error())
        flask.abort(500)
    old_motd = fleet_settings.get_motd()

    wait_for_change = False
    # check number of wings
    
    fleet_wings = fleet_api.get_wings()
    
    num_wings = len(fleet_wings.wings())
    if num_wings <= 0:
        fleet_api.create_wing()  # create 1st wing
        fleet_api.create_wing()  # create 2nd wing
        wait_for_change = True
    elif num_wings <= 1:
        fleet_api.create_wing()  # create 2nd wing
        wait_for_change = True

    ts_string = ""
    ts_id = sget_active_ts_id()
    if ts_id is not None:
        teamspeak = db.session.query(TeamspeakDatum).get(ts_id)
        ts_string = teamspeak.displayHost
        if teamspeak.displayPort != 9987:
            ts_string = ts_string + ":" + str(teamspeak.displayPort)
    
    if len(old_motd) < 50:
        
        new_motd = ""
        if fleet_type == "hq":
            hq_motd = sget_motd_hq()
            
            if hq_motd is not None:
                new_motd = hq_motd
    
        elif fleet_type == "vg":
            vg_motd = sget_motd_vg()
            
            if vg_motd is not None:
                new_motd = vg_motd
        
        fleet_api.set_fleet_settings(False, new_motd.replace("$ts$", ts_string))

    if wait_for_change:
        sleep(6)

    wait_for_change = False

    wing_ongrid = wing_offgrid = None
    for wing in fleet_api.get_wings().wings():
        if wing.name() == "Wing 1" or wing.name().lower() == "on grid":
            wing_ongrid = wing
        elif wing.name() == "Wing 2" or wing.name().lower() == "off grid":
            wing_offgrid = wing

    if wing_ongrid is None or wing_offgrid is None:
        return None

    # Set up wing names
    if wing_ongrid.name().lower() != "on grid":
        wait_for_change = True
        fleet_api.set_wing_name(wing_ongrid.id(), 'ON GRID')
    if wing_offgrid.name().lower() != "off grid":
        fleet_api.set_wing_name(wing_offgrid.id(), 'OFF GRID')

    # make sure there is enough squads, otherwise create them
    # the -1 is needed because of the queue list
    num_needed_squads: int = len(waitlistGroup.waitlists)-1
    num_squads = len(wing_ongrid.squads())
    if num_squads < num_needed_squads:
        for _ in range(num_needed_squads-num_squads):
            wait_for_change = True
            fleet_api.create_squad(wing_ongrid.id())


    # create 1 squad for the offgrid win, if there is none
    num_squads = len(wing_offgrid.squads())
    if num_squads < 1:
        wait_for_change = True
        fleet_api.create_squad(wing_offgrid.id())

    if wait_for_change:
        sleep(6)

    wings = fleet_api.get_wings()
    for wing in wings.wings():
        if wing.name().lower() == "on grid":
            wing_ongrid = wing
        elif wing.name().lower() == "off grid":
            wing_offgrid = wing

    if wing_ongrid is None or wing_offgrid is None:
        return None

    waitlist: Waitlist
    for idx, waitlist in enumerate(filter(lambda w: w.id != waitlistGroup.queueID, waitlistGroup.waitlists), 1):
        for squad in wing_ongrid.squads():
            if squad.name() == ('Squad '+str(idx)):
                fleet_api.set_squad_name(squad.id(), waitlist.displayTitle)

    if wing_offgrid is not None and len(wing_offgrid.squads()) > 0 and wing_offgrid.squads()[0].name().lower() != "off grid":
        fleet_api.set_squad_name(wing_offgrid.squads()[0].id(), 'OFF GRID')
    
    sleep(5)
    return None


def invite(user_id: int, squad_id_list: Sequence[Tuple[int, int]]):
    token: Optional[SSOToken] = current_user.get_a_sso_token_with_scopes(esi_scopes.fleet_write)
    if token is None:
        return {'status_code': 404, 'text': "You need to go to <a href='" + url_for('fc_sso.login_redirect') +
                                            "'>SSO Login</a> and relogin in!"}

    fleet: CrestFleet = current_user.fleet
    fleet_api: EveFleetEndpoint = EveFleetEndpoint(token, fleet.fleetID)
    oldsquad = (0, 0)
    for idx in range(len(squad_id_list)):
        squad = squad_id_list[idx]
        if squad[0] == oldsquad[0] and squad[1] == oldsquad[1]:
            continue
        logger.info("Invite %s to wingID %s and squadID %s", str(user_id), str(squad[0]), str(squad[1]))

        try:
            response = fleet_api.invite(user_id, 'squad_member', squad[1], squad[0])
        except Exception as ex:
            logger.error("Failed to Invite Member[%d] into squad[%d] wing[%d]", user_id, squad[0], squad[1])
            raise ex
        if response.is_error():
            logger.info('Got code[%d] back from invite call', response.code())
            if response.is_monolith_error():
                mono_error = response.get_monolith_error()
                if mono_error['error_label'] == 'FleetTooManyMembersInSquad':
                    logger.info(f'Failed to invites because there are to many people in this squad'
                                f' {mono_error["error_dict"]["num"]} ... trying next one')
                    continue
                elif mono_error['error_label'] == 'FleetCandidateOffline':
                    logger.info('Failed invite because target player is offline.')
                    return {'status_code': 520, 'text': 'They player you tried to invite was offline.'}
                elif mono_error['error_label'] == 'ContactOwnerUnreachable':
                    logger.info(f'Failed to invite {mono_error["error_dict"]["name"]}'
                                f' because he has the invitee blocked')
                    return {'status_code': 520, 'text': f'Could not invite {mono_error["error_dict"]["name"]}'
                                                        f' because he has you blocked or is otherwise unreachable.'}
                else:
                    logger.error(f'Failed invite because of monolith error {response.error()}')
                    return {'status_code': 520, 'text': f'Failed invite because of unhandled Monolith error '
                                                        f'{response.error()} please report this to the waitlist '
                                                        f'maintainer with the monolith message.'}
            elif response.code() == 404:
                return {'status_code': 404, 'text': "You need to go to <a href='" + url_for('fc_sso.login_redirect') +
                                                    "'>SSO Login</a> and relogin in!"}
            else:
                return {'status_code': response.code(), 'text': response.error()}

        return {'status_code': response.code(),
                'text': 'Invite failed for unknown reason'}

    logger.info("Failed to invite %d to a squad, because all squads are full!", user_id)
    return {'status_code': 403, 'text': 'Failed to invite person a squad, all squads are full!'}


def spawn_invite_check(character_id, group_id, fleet_id):
    logger.info(f"Spawning invite check timer for character_id={character_id} group_id={group_id}"
                f" and fleet_id={fleet_id}")
    timer_id = (character_id, group_id, fleet_id)
    if timer_id in check_timers:  # this invite check is already running
        logger.info(f"There is already an invite check running for {timer_id}")
        return
    check_timers[timer_id] = 0
    t = Timer(20.0, check_invite_and_remove_timer,
              [character_id, group_id, fleet_id])
    t.start()
    logger.debug(f'Started timer for {timer_id}')


check_timers: Dict[Tuple[int, int, int], int] = dict()


def check_invite_and_remove_timer(char_id: int, group_id: int, fleet_id: int):
    try:
        logger.info(f"Check Invite and remove timer triggered for"
                    f" char_id={char_id}, group_id={group_id} and fleet_id={fleet_id}")
        max_runs: int = 4
        current_run: int = 1
        timer_id = (char_id, group_id, fleet_id)
        if timer_id in check_timers:
            current_run = check_timers[timer_id]+1

        check_timers[timer_id] = current_run
        logger.info(f"New Timer count={check_timers[timer_id]} for timer_id={timer_id}")

        # hold SSE till sending
        _events = []
        logger.info("Checking invite for charID[%d] groupID[%d] fleetID[%d] current_run[%d]",
                    char_id, group_id, fleet_id, current_run)
        group: WaitlistGroup = db.session.query(WaitlistGroup).get(group_id)
        crest_fleet = db.session.query(CrestFleet).get(fleet_id)
        # the fleet was deleted meanwhile or has no fleetcomp
        if group is None or crest_fleet is None or crest_fleet.comp is None:
            if group is None:
                logger.error("On Invitecheck group is None")
            if crest_fleet is None:
                logger.error("On Invitecheck crestFleet is None")
            elif crest_fleet.comp is None:
                logger.error("On Invitecheck FleetComp is None")
            db.session.remove()
            return
        with member_info:
            member = member_info.get_fleet_members(fleet_id, crest_fleet.comp)
        character = db.session.query(Character).filter(Character.id == char_id).first()
        waitlist_entries = db.session.query(WaitlistEntry)\
            .filter((WaitlistEntry.user == char_id) &
                    (WaitlistEntry.waitlist_id != group.queueID)
                    ).all()

        if member is not None and char_id in member:  # he is in the fleet
            logger.info("Member %s found in members", char_id)
            fittings = []
            for entry in waitlist_entries:
                fittings.extend(entry.fittings)

            for entry in waitlist_entries:
                event = EntryRemovedSSE(entry.waitlist.group.groupID,
                                        entry.waitlist_id, entry.id)
                _events.append(event)

            db.session.query(WaitlistEntry).filter(
                (WaitlistEntry.user == char_id) &
                (WaitlistEntry.waitlist_id != group.queueID)
            ).delete()

            h_entry = create_history_object(char_id, HistoryEntry.EVENT_AUTO_RM_PL, None, fittings)
            h_entry.exref = group.groupID
            db.session.add(h_entry)
            db.session.commit()

            for event in _events:
                send_server_sent_event(event)

            logger.info("auto removed %s from %s waitlist.", character.eve_name, group.groupName)
            # we are done delete timer entry
            check_timers.pop(timer_id, None)
        else:
            logger.info("Character %d %s not found in fleetmembers", char_id, character.eve_name)
            if current_run == max_runs:  # he reached his invite timeout
                logger.info("Max Runs reached and Member %s not found in members", str(char_id))
                for entry in waitlist_entries:
                    entry.inviteCount += 1
                h_entry = create_history_object(char_id, HistoryEntry.EVENT_AUTO_CHECK_FAILED, None, None)
                h_entry.exref = group.groupID
                db.session.add(h_entry)
                db.session.commit()
                send_server_sent_event(InviteMissedSSE(group_id, char_id))

                logger.info("%s missed his invite", character.eve_name)
                # we are done delete the timer entry
                check_timers.pop(timer_id, None)
            else:
                # we want to wait some more, set up new timer
                logger.info('charID[%d] groupID[%d] fleetID[%d] %s was not in fleet this time, checking again in 20s',
                            char_id, group_id, fleet_id, character.eve_name)
                t = Timer(20.0, check_invite_and_remove_timer, [char_id, group_id, fleet_id])
                t.start()

        db.session.remove()
    except Exception:
        logger.exception("Some thing went wrong during invite check!")
