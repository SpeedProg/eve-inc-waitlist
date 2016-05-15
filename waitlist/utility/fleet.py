from flask_login import current_user
from pycrest.eve import AuthedConnectionB
from waitlist.utility.config import crest_client_id, crest_client_secret,\
    motd_hq, motd_vg
from time import sleep
import logging
from threading import Timer
from waitlist.base import db
from waitlist.storage.database import WaitlistGroup, CrestFleet, WaitlistEntry,\
    HistoryEntry, Character, TeamspeakDatum
from datetime import datetime, timedelta
from waitlist.utility.history_utils import create_history_object
from pycrest.errors import APIException
from waitlist.utility.crest import create_token_cb
from flask.helpers import url_for
from waitlist.utility.settings.settings import sget_active_ts_id, sget_motd_hq,\
    sget_motd_vg

logger = logging.getLogger(__name__)

class FleetMemberInfo():
    def __init__(self):
        self._lastupdate = {}
        self._lastmembers = {}
    
    def get_fleet_members(self, fleetID, account):
        return self.get_data(fleetID, account)
    
    def _json_to_members(self, json):
        data = {}
        for member in json.items:
            data[member.character.id] = member
        return data
    
    def get_data(self, fleetID, account):
        utcnow = datetime.utcnow()
        if (self.is_expired(fleetID, utcnow)):
            fleet = connection_cache.get_connection(fleetID, account)
            try:
                json = fleet().members()
                self.update_cache(fleetID, utcnow, self._json_to_members(json))
            except APIException:
                self.update_cache(fleetID, utcnow, {})
        
        return self._lastmembers[fleetID]
    
    def is_expired(self, fleetID, utcnow):
        if not fleetID in self._lastupdate:
            return True
        else:
            lastUpdated = self._lastupdate[fleetID]
            if utcnow - lastUpdated < timedelta(seconds=5):
                return False
            else:
                return True
    
    def update_cache(self, fleetID, utcnow, data):
        self._lastmembers[fleetID] = data
        self._lastupdate[fleetID] = utcnow

class FleetConnectionCache():
    def __init__(self):
        self._cache = {}
    
    def get_connection(self, fleetID, account):
        if account.id in self._cache:
            con = self._cache[account.id]
            con.update_tokens(account.refresh_token, account.access_token, account.access_token_expires)
            return con
        else:
            return self._add_connection(fleetID, account)
    
    def _add_connection(self, fleetID, account):
        fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleetID)+"/"
        data = {
            'access_token': account.access_token,
            'refresh_token': account.refresh_token,
            'expires_in': account.access_token_expires
            }
        connection = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(account.id()))
        self._cache[account.id] = connection
        return connection

connection_cache = FleetConnectionCache()
member_info = FleetMemberInfo()

class FleetRoles():
    SQUAD_COMMANDER = 'squadCommander'
    SQUAD_MEMBER = 'squadMember'
    WING_COMMANDER = 'wingCommander'
    FLEET_COMMANDER = 'fleetCommander'

def setup(fleet_id, fleet_type):
    fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleet_id)+"/"
    data = {
            'access_token': current_user.access_token,
            'refresh_token': current_user.refresh_token,
            'expires_in': current_user.access_token_expires
            }
    fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
    fleet()
    wait_for_change = False
    # check number of wings
    num_wings = len(fleet().wings().items)
    if num_wings <= 0:
        fleet.wings.post() # create 1st wing
        fleet.wings.post() # create 2nd wing
        wait_for_change = True
    elif num_wings <= 1:
        fleet.wings.post() # create 2 squad
        wait_for_change = True

    tsString = ""
    tsID = sget_active_ts_id()
    if tsID is not None:
        teamspeak = db.session.query(TeamspeakDatum).get(tsID)
        tsString = teamspeak.displayHost
        if teamspeak.displayPort != 9987:
            tsString = tsString + ":" + str(teamspeak.displayPort)
    if fleet_type == "hq":
        fleet.put(fleet_url,json={'isFreeMove':True,'motd':sget_motd_hq().replace("$ts$", tsString)})
    elif fleet_type == "vg":
        fleet.put(fleet_url,json={'isFreeMove':True,'motd':sget_motd_vg().replace("$ts$", tsString)})

    if wait_for_change:
        sleep(6)
    
    wait_for_change = False

    wing1 = wing2 = None
    for wing in fleet.wings().items:
        if wing.name == "Wing 1" or wing.name.lower() == "on grid":
            wing1 = wing
        elif wing.name == "Wing 2" or wing.name.lower() == "tipping":
            wing2 = wing
    
    if wing1 is None or wing2 is None:
        return
    
    if wing1.name.lower() != "on grid":
        wait_for_change = True
        wing1.put(json={'name':'ON GRID'})

    num_needed_squads = 4 if fleet_type == "hq" else 2
    num_squads = len(wing1.squadsList)
    if num_squads < num_needed_squads:
        for _ in range(num_needed_squads-num_squads):
            wait_for_change = True
            wing1.squads.post()


    if wing2.name.lower() != "tipping":
        wing2.put(json={'name':'Tipping'})

    num_squads = len(wing2.squadsList)
    if num_squads < 1:
        wait_for_change = True
        wing2.squads.post() # create 1 squad

    if wait_for_change:
        sleep(6)

    wings = fleet().wings()
    for wing in wings.items:
        if wing.name.lower() == "on grid":
            wing1 = wing
        elif wing.name.lower() == "tipping":
            wing2 = wing
    
    if wing1 is None or wing2 is None:
        return
    
    logiSquad = sniperSquad = dpsSquad = moreDpsSquad = None

    for squad in wing1.squadsList:
        if squad.name == "Squad 1" or squad.name.lower() == "logi":
            logiSquad = squad
        elif squad.name == "Squad 2" or squad.name.lower() == "sniper":
            sniperSquad = squad
        elif squad.name == "Squad 3" or squad.name.lower() == "dps":
            dpsSquad = squad
        elif squad.name == "Squad 4" or squad.name.lower() == "more dps" or squad.name.lower() == "other":
            moreDpsSquad = squad
    
    if fleet_type == "hq":
        if logiSquad is not None and logiSquad.name == "Squad 1":
            logiSquad.put(json={'name':'LOGI'})
        if sniperSquad is not None and sniperSquad.name == "Squad 2":
            sniperSquad.put(json={'name':'SNIPER'})
        if dpsSquad is not None and dpsSquad.name == "Squad 3":
            dpsSquad.put(json={'name':'DPS'})
        if moreDpsSquad is not None and moreDpsSquad.name == "Squad 4":
            moreDpsSquad.put(json={'name':'MORE DPS'})
    elif fleet_type == "vg":
        if logiSquad is not None and logiSquad.name == "Squad 1":
            logiSquad.put(json={'name':'LOGI'})
        if sniperSquad is not None and sniperSquad.name == "Squad 2":
            sniperSquad.put(json={'name':'DPS'})
    

    if wing2 is not None and wing2.squadsList is not None and wing2.squadsList[0].name.lower() != "tipping":
        wing2.squadsList[0].put(json={'name':'Tipping'})
    
    sleep(5)

def get_wings(fleet_id):
    try:
        fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleet_id)+"/"
        data = {
                'access_token': current_user.access_token,
                'refresh_token': current_user.refresh_token,
                'expires_in': current_user.access_token_expires
                }
        fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
        return fleet().wings().items
    except APIException as ex:
        logger.error("CREST failed with %s : %s", str(ex.resp.status_code), ex.resp.json())
        raise ex

def invite(user_id, squadIDList):
    fleet = current_user.fleet
    fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleet.fleetID)+"/"
    data = {
            'access_token': current_user.access_token,
            'refresh_token': current_user.refresh_token,
            'expires_in': current_user.access_token_expires
            }
    try:
        fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret, create_token_cb(current_user.id))
        oldsquad = (0, 0)
        for idx in xrange(len(squadIDList)-1):
            squad = squadIDList[idx];
            if squad[0] == oldsquad[0] and squad[1] == oldsquad[1]:
                continue
            logger.info("Invite %s to wingID %s and squadID %s", str(user_id), str(squad[0]), str(squad[1]))
    
            try:
                resp = fleet().members.post(json={'role':'squadMember', 'wingID': squad[0], 'squadID': squad[1], 'character':{'href':'https://crest-tq.eveonline.com/characters/'+str(user_id)+'/'}})
            except APIException as ex:
                if ex.resp.status_code == 403:
                    return {'status_code': ex.resp.status_code, 'text': ex.resp.json()['message']}
                else:
                    raise ex
                
            if resp.status_code == 403:
                if resp.json()['key'] == "FleetTooManyMembersInSquad":
                    continue
                else:
                    return {'status_code': resp.status_code, 'text': resp.json()['message']}
            elif resp.status_code == 201:
                return {'status_code': 201, 'text': resp.text}
            else:
                return {'status_code': resp.status_code, 'text': resp.json()['message']}
    except APIException as ex:
        if ex.resp.status_code == 400:
                return {'status_code': 400, 'text': "You need to go to <a href='"+url_for('fc_sso.login_redirect')+"'>SSO Login</a> and relogin in!"}
        else:
            logger.error("CREST failed with %s : %s", str(ex.resp.status_code), ex.resp.json())
            return {'status_code': ex.resp.status_code, 'text': ex.resp.json()['error_description']}
    return {'status_code': 403, 'text': 'Failed to invite person a a squad, all squads are full!'}

def spawn_invite_check(characterID, groupID, fleetID):
    t = Timer(66.0, check_invite_and_remove_timer, [characterID, groupID, fleetID])
    t.start()

def check_invite_and_remove_timer(charID, groupID, fleetID):
    group = db.session.query(WaitlistGroup).get(groupID)
    crestFleet = db.session.query(CrestFleet).get(fleetID)
    if group is None or crestFleet is None or crestFleet.comp is None: # the fleet was deleted meanwhile or has no fleetcomp
        return
    member = member_info.get_fleet_members(fleetID, crestFleet.comp)
    character = db.session.query(Character).filter(Character.id == charID).first()
    waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) &
                                                   ((WaitlistEntry.waitlist_id == group.logiwlID) |
                                                     (WaitlistEntry.waitlist_id == group.dpswlID) |
                                                     (WaitlistEntry.waitlist_id == group.sniperwlID))).all()
    if charID in member:# he is in the fleet
        fittings = []
        for entry in waitlist_entries:
            fittings.extend(entry.fittings)
        
        # check if there is an other waitlist
        if group.otherwlID is not None:
            entry = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) & (WaitlistEntry.waitlist_id == group.otherwlID)).on_or_none()
            if entry is not None:
                fittings.extend(entry.fittings)
        
        
        waitlist_entries = db.session.query(WaitlistEntry).filter((WaitlistEntry.user == charID) &
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

        logger.info("auto removed %s from %s waitlist.", character.eve_name, group.groupName)
    else:
        for entry in waitlist_entries:
            entry.inviteCount += 1
        hEntry = create_history_object(charID, HistoryEntry.EVENT_AUTO_CHECK_FAILED, None, None)
        hEntry.exref = group.groupID
        db.session.add(hEntry)
        db.session.commit()
        logger.info("%s missed his invite", character.eve_name)
        
