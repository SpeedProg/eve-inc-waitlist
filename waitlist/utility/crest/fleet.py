from flask_login import current_user
from pycrest.eve import AuthedConnectionB
from waitlist.utility.config import crest_client_id, crest_client_secret,\
    motd_hq, motd_vg
from time import sleep
import logging

logger = logging.getLogger(__name__)

class FleetConnectionCache():
    def __init__(self):
        self._cache = {}
    
    def get_connection(self, fleetID, account):
        if account.id in self._cache:
            return self._cache[account.id].update_tokens(account.refresh_token, account.access_token, account.access_token_expires)
        else:
            return self._add_connection(fleetID, account)
    
    def _add_connection(self, fleetID, account):
        fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleetID)+"/"
        data = {
            'access_token': account.access_token,
            'refresh_token': account.refresh_token,
            'expires_in': account.access_token_expires
            }
        connection = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret)
        self._cache[account.id] = connection
        return connection

connection_cache = FleetConnectionCache()

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
    fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret)
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

    if fleet_type == "hq":
        fleet.put(fleet_url,json={'isFreeMove':True,'motd':motd_hq})
    elif fleet_type == "vg":
        fleet.put(fleet_url,json={'isFreeMove':True,'motd':motd_vg})

    if wait_for_change:
        sleep(6)
    
    wait_for_change = False

    wing1 = wing2 = None
    for wing in fleet.wings().items:
        if wing.name == "Wing 1" or wing.name.lower() == "on grid":
            print "Found wing1"
            wing1 = wing
        elif wing.name == "Wing 2" or wing.name.lower() == "tipping":
            print "Found wing2"
            wing2 = wing

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
    print wings
    for wing in wings.items:
        if wing.name.lower() == "on grid":
            print "Found wing1"
            wing1 = wing
        elif wing.name.lower() == "tipping":
            print "Found wing2"
            wing2 = wing
    
    logiSquad = sniperSquad = dpsSquad = moreDpsSquad = None
    print wing1
    for squad in wing1.squadsList:
        if squad.name == "Squad 1" or squad.name.lower() == "logi":
            print "found "+ squad.name
            logiSquad = squad
        elif squad.name == "Squad 2" or squad.name.lower() == "sniper":
            print "found "+ squad.name
            sniperSquad = squad
        elif squad.name == "Squad 3" or squad.name.lower() == "dps":
            print "found "+ squad.name
            dpsSquad = squad
        elif squad.name == "Squad 4" or squad.name.lower() == "more dps" or squad.name.lower() == "other":
            print "found "+ squad.name
            moreDpsSquad = squad
        else:
            print squad.name
    
    if fleet_type == "hq":
        if logiSquad.name == "Squad 1":
            logiSquad.put(json={'name':'LOGI'})
        if sniperSquad.name == "Squad 2":
            sniperSquad.put(json={'name':'SNIPER'})
        if dpsSquad.name == "Squad 3":
            dpsSquad.put(json={'name':'DPS'})
        if moreDpsSquad.name == "Squad 4":
            moreDpsSquad.put(json={'name':'MORE DPS'})
    elif fleet_type == "vg":
        if logiSquad.name == "Squad 1":
            logiSquad.put(json={'name':'LOGI'})
        if sniperSquad.name == "Squad 2":
            sniperSquad.put(json={'name':'DPS'})
    

    if wing2.squadsList[0].name.lower() != "tipping":
        wing2.squadsList[0].put(json={'name':'Tipping'})
    
    sleep(5)

def get_wings(fleet_id):
    fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleet_id)+"/"
    data = {
            'access_token': current_user.access_token,
            'refresh_token': current_user.refresh_token,
            'expires_in': current_user.access_token_expires
            }
    fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret)
    print fleet().members()
    return fleet().wings().items

def invite(user_id, squadIDList):
    fleet = current_user.fleet
    fleet_url = "https://crest-tq.eveonline.com/fleets/"+str(fleet.fleetID)+"/"
    data = {
            'access_token': current_user.access_token,
            'refresh_token': current_user.refresh_token,
            'expires_in': current_user.access_token_expires
            }
    fleet = AuthedConnectionB(data, fleet_url, "https://login.eveonline.com/oauth", crest_client_id, crest_client_secret)
    oldsquad = (0, 0)
    for idx in xrange(len(squadIDList)-1):
        squad = squadIDList[idx];
        if squad[0] == oldsquad[0] and squad[1] == oldsquad[1]:
            continue
        logger.info("Invite %s to wingID %s and squadID %s", str(user_id), str(squad[0]), str(squad[1]))
        resp = fleet().members.post(json={'role':'squadMember', 'wingID': squad[0], 'squadID': squad[1], 'character':{'href':'https://crest-tq.eveonline.com/characters/'+str(user_id)+'/'}})
        print resp
        print resp.text
        if resp.status_code == 403:
            if resp.json()['key'] == "FleetTooManyMembersInSquad":
                continue
            else:
                return {'status_code': resp.status_code, 'text': resp.json().message}
        elif resp.status_code == 201:
            return {'status_code': 201, 'text': resp.text}
        else:
            return {'status_code': resp.status_code, 'text': resp.json().message}

    return {'status_code': 403, 'text': 'Failed to invite person a a squad, all squads are full!'}