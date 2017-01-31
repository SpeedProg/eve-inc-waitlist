from flask_login import current_user
from time import sleep
import logging
from threading import Timer
from waitlist.base import db
from waitlist.storage.database import WaitlistGroup, CrestFleet, WaitlistEntry,\
    HistoryEntry, Character, TeamspeakDatum
from datetime import datetime
from waitlist.utility.history_utils import create_history_object
from flask.helpers import url_for
from waitlist.utility.settings.settings import sget_active_ts_id, sget_motd_hq,\
    sget_motd_vg
from waitlist.data.sse import sendServerSentEvent, InviteMissedSSE,\
    EntryRemovedSSE
from waitlist.utility.swagger.eve.fleet import EveFleetEndpoint

logger = logging.getLogger(__name__)

class FleetMemberInfo():
    def __init__(self):
        self._cached_until = {}
        self._lastmembers = {}
    
    def get_fleet_members(self, fleetID, account):
        return self._get_data(fleetID, account)
    
    def _to_members_map(self, response):
        # type: (FleetMembers) -> dict(int, FleetMember)
        data = {}
        logger.debug("Got MemberList from API %s", str(response))
        for member in response.FleetMember():
            data[member.characterID()] = member
        return data
    
    def _get_data(self, fleetID, account):
        fleetApi = EveFleetEndpoint(fleetID)
        utcnow = datetime.utcnow()
        if (self._is_expired(fleetID, utcnow)):
            logger.debug("Member Data Expired for %d and account %s", fleetID, account.username)
            try:
                logger.debug("%s Requesting Fleet Member", account.username)
                data = fleetApi.get_member()
                if not data.is_error():
                    logger.debug("%s Got Fleet Members", account.username)
                    self._update_cache(fleetID, self._to_members_map(data.data), data.expires)
                    logger.debug("%s Successfully updated Fleet Members", account.username)
                else:
                    logger.error("Failed to get Fleetmembers from API code[%d] msg[%s]", data.code(), data.error())
                    return self.get_cache_data(fleetID)
            except Exception as ex:
                logger.error("%s Getting Fleet Members caused: %s", account.username, ex)
                return self.get_cache_data(fleetID)
        else:
            logger.debug("Cache hit for %d and account %s", fleetID, account.username)
        return self._lastmembers[fleetID]
    
    def get_cache_data(self, fleetID):
        if (fleetID in self._lastmembers):
            return self._lastmembers[fleetID]
        return None
    
    def _is_expired(self, fleetID, utcnow):
        if not fleetID in self._cached_until:
            return True
        else:
            expires_at = self._cached_until[fleetID]
            if utcnow < expires_at:
                return False
            else:
                return True
    
    def _update_cache(self, fleetID, members):
        # type: (int, FleetMember)
        self._lastmembers[fleetID] = self._to_members_map(members)
        self._cached_until[fleetID] = members.expires()

member_info = FleetMemberInfo()

def setup(fleet_id, fleet_type):
    # type: (int, str) -> boolean
    fleetApi = EveFleetEndpoint(fleet_id)
    fleet_settings = fleetApi.get_fleet_settings()

    old_motd = fleet_settings.get_MOTD()

    wait_for_change = False
    # check number of wings
    
    fleet_wings = fleetApi.get_wings()
    
    num_wings = len(fleet_wings.wings())
    if num_wings <= 0:
        fleetApi.create_wing() # create 1st wing
        fleetApi.create_wing() # create 2nd wing
        wait_for_change = True
    elif num_wings <= 1:
        fleetApi.create_wing() # create 2nd wing
        wait_for_change = True

    tsString = ""
    tsID = sget_active_ts_id()
    if tsID is not None:
        teamspeak = db.session.query(TeamspeakDatum).get(tsID)
        tsString = teamspeak.displayHost
        if teamspeak.displayPort != 9987:
            tsString = tsString + ":" + str(teamspeak.displayPort)
    
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
        
        fleetApi.set_fleet_settings(False, new_motd.replace("$ts$", tsString))

    if wait_for_change:
        sleep(6)
    
    wait_for_change = False

    wing1 = wing2 = None
    for wing in fleetApi.get_wings().wings():
        if wing.name() == "Wing 1" or wing.name().lower() == "on grid":
            wing1 = wing
        elif wing.name() == "Wing 2" or wing.name().lower() == "tipping":
            wing2 = wing
    
    if wing1 is None or wing2 is None:
        return
    
    if wing1.name().lower() != "on grid":
        wait_for_change = True
        fleetApi.set_wing_name(wing1.id(), 'ON GRID')

    num_needed_squads = 4 if fleet_type == "hq" else 2
    num_squads = len(wing1.squads())
    if num_squads < num_needed_squads:
        for _ in range(num_needed_squads-num_squads):
            wait_for_change = True
            fleetApi.create_squad(wing1.id())


    if wing2.name().lower() != "tipping":
        fleetApi.set_wing_name(wing2.id(), 'Tipping')

    num_squads = len(wing2.squads())
    if num_squads < 1:
        wait_for_change = True
        fleetApi.create_squad(wing2.id())

    if wait_for_change:
        sleep(6)

    wings = fleetApi.get_wings()
    for wing in wings.wings():
        if wing.name().lower() == "on grid":
            wing1 = wing
        elif wing.name().lower() == "tipping":
            wing2 = wing
    
    if wing1 is None or wing2 is None:
        return
    
    logiSquad = sniperSquad = dpsSquad = moreDpsSquad = None

    for squad in wing1.squads():
        if squad.name() == "Squad 1" or squad.name().lower() == "logi":
            logiSquad = squad
        elif squad.name() == "Squad 2" or squad.name().lower() == "sniper":
            sniperSquad = squad
        elif squad.name() == "Squad 3" or squad.name().lower() == "dps":
            dpsSquad = squad
        elif squad.name() == "Squad 4" or squad.name().lower() == "more dps" or squad.name().lower() == "other":
            moreDpsSquad = squad
    
    if fleet_type == "hq":
        if logiSquad is not None and logiSquad.name() == "Squad 1":
            fleetApi.set_squad_name(logiSquad.id(), 'LOGI')
        if sniperSquad is not None and sniperSquad.name() == "Squad 2":
            fleetApi.set_squad_name(sniperSquad.id(), 'LOGI')
        if dpsSquad is not None and dpsSquad.name == "Squad 3":
            fleetApi.set_squad_name(dpsSquad.id(), 'DPS')
        if moreDpsSquad is not None and moreDpsSquad.name == "Squad 4":
            fleetApi.set_squad_name(moreDpsSquad.id(), 'MORE DPS')
    elif fleet_type == "vg":
        if logiSquad is not None and logiSquad.name == "Squad 1":
            fleetApi.set_squad_name(logiSquad.id(), 'LOGI')
        if sniperSquad is not None and sniperSquad.name == "Squad 2":
            fleetApi.set_squad_name(sniperSquad.id(), 'DPS')

    if wing2 is not None and len(wing2.squads()) > 0 and wing2.squad()[0].name().lower() != "tipping":
        fleetApi.set_squad_name(wing2.squads()[0].id(), 'Tipping')
    
    sleep(5)

def invite(user_id, squadIDList):
    fleet = current_user.fleet
    fleetApi = EveFleetEndpoint(fleet.fleetID)
    oldsquad = (0, 0)
    for idx in xrange(len(squadIDList)):
        squad = squadIDList[idx];
        if squad[0] == oldsquad[0] and squad[1] == oldsquad[1]:
            continue
        logger.info("Invite %s to wingID %s and squadID %s", str(user_id), str(squad[0]), str(squad[1]))

        try:
            response = fleetApi.invite(user_id, 'squad_member', squad[1], squad[0])
        except Exception as ex:
            logger.error("Failed to Invite Member[%d] into squad[%d] wing[%d]", user_id, squad[0], squad[1])
            raise ex
        if response.is_error():
            logger.info('Got code[%d] back from invite call', response.code())
            if response.code() == 422:
                continue
            elif response.code() == 404:
                return {'status_code': 404, 'text': "You need to go to <a href='"+url_for('fc_sso.login_redirect')+"'>SSO Login</a> and relogin in!"}
            else:
                return {'status_code': response.code(), 'text': response.error()}

        return {'status_code': response.code(), 'text': ''}

    logger.info("Failed to invite %d to a squad, because all squads are full!", user_id)
    return {'status_code': 403, 'text': 'Failed to invite person a squad, all squads are full!'}

def spawn_invite_check(characterID, groupID, fleetID):
    timerID = (characterID, groupID, fleetID)
    if timerID in check_timers: # this invite check is already running
        return
    check_timers[timerID] = 0
    t = Timer(20.0, check_invite_and_remove_timer, [characterID, groupID, fleetID])
    t.start()

check_timers = dict()

def check_invite_and_remove_timer(charID, groupID, fleetID):
    max_runs = 4
    current_run = 1
    timerID = (charID, groupID, fleetID)
    if timerID in check_timers:
        current_run = check_timers[timerID]+1
    
    check_timers[timerID] = current_run
    
    # hold SSE till sending
    _events = []
    logger.info("Checking invite for charID[%d] groupID[%d] fleetID[%d] current_run[%d]", charID, groupID, fleetID, current_run)
    group = db.session.query(WaitlistGroup).get(groupID)
    crestFleet = db.session.query(CrestFleet).get(fleetID)
    if group is None or crestFleet is None or crestFleet.comp is None: # the fleet was deleted meanwhile or has no fleetcomp
        if group is None:
            logger.error("On Invitecheck group is None")
        if crestFleet is None:
            logger.error("On Invitecheck crestFleet is None")
        elif crestFleet.comp is None:
            logger.error("On Invitecheck FleetComp is None")
        db.session.remove()
        return
    member = member_info.get_fleet_members(fleetID, crestFleet.comp)
    character = db.session.query(Character).filter(Character.id == charID).first()
    waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) &
                                                   ((WaitlistEntry.waitlist_id == group.logiwlID) |
                                                     (WaitlistEntry.waitlist_id == group.dpswlID) |
                                                     (WaitlistEntry.waitlist_id == group.sniperwlID))).all()
    if charID in member:# he is in the fleet
        logger.info("Member %s found in members", charID)
        fittings = []
        for entry in waitlist_entries:
            fittings.extend(entry.fittings)
        
        # check if there is an other waitlist
        if group.otherwlID is not None:
            entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) & (WaitlistEntry.waitlist_id == group.otherwlID)).on_or_none()
            if entry is not None:
                fittings.extend(entry.fittings)
        
        for entry in waitlist_entries:
            event = EntryRemovedSSE(entry.waitlist.groupID, entry.waitlist_id, entry.id)
            _events.append(event)
        
        db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) &
                                                                   ((WaitlistEntry.waitlist_id == group.logiwlID) |
                                                                     (WaitlistEntry.waitlist_id == group.dpswlID) |
                                                                     (WaitlistEntry.waitlist_id == group.sniperwlID))).delete()
        # if other waitlist delete those entries too
        if group.otherwlID is not None:
            entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) & (WaitlistEntry.waitlist_id == group.otherwlID)).delete()
        
        hEntry = create_history_object(charID, HistoryEntry.EVENT_AUTO_RM_PL, None, fittings)
        hEntry.exref = group.groupID
        db.session.add(hEntry)
        db.session.commit()
        
        for event in _events:
            sendServerSentEvent(event)

        logger.info("auto removed %s from %s waitlist.", character.eve_name, group.groupName)
        # we are done delete timer entry
        check_timers.pop(timerID, None)
    else:
        logger.info("Character %d %s not found in fleetmembers", charID, character.eve_name)
        if current_run == max_runs: # he reached his invite timeout
            logger.info("Max Runs reached and Member %s not found in members", str(charID))
            for entry in waitlist_entries:
                entry.inviteCount += 1
            hEntry = create_history_object(charID, HistoryEntry.EVENT_AUTO_CHECK_FAILED, None, None)
            hEntry.exref = group.groupID
            db.session.add(hEntry)
            db.session.commit()
            sendServerSentEvent(InviteMissedSSE(groupID, charID))
    
            logger.info("%s missed his invite", character.eve_name)
            # we are done delete the timer entry
            check_timers.pop(timerID, None)
        else:
            # we want to wait some more, set up new timer
            logger.info('charID[%d] groupID[%d] fleetID[%d] %s was not in fleet this time, checking again in 20s', charID, groupID, fleetID, character.eve_name)
            t = Timer(20.0, check_invite_and_remove_timer, [charID, groupID, fleetID])
            t.start()
    
    db.session.remove()
