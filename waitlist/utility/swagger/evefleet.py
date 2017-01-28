from msilib.schema import ControlEvent
def get_members(fleetID):
    security = EsiSecurity(
        api,
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': current_user.ssoToken.access_token,
        'expires_in': (current_user.ssoToken.access_token_expires - datetime.utcnow()).total_seconds(),
        'refresh_token': current_user.ssoToken.refresh_token
    })
    client = EsiClient(security)
    response = client.request(api.op['get_fleets_fleet_id_members'](fleet_id=fleetID))
    cacheTime = header_to_datetime(response.header['Expires'][0])

    return {'expires': cacheTime, 'data': response.data, 'response': response}

def invite_member(fleetID, characterID, role, squadID, wingID):
    security = EsiSecurity(
        api,
        crest_return_url,
        crest_client_id,
        crest_client_secret
    )
    security.update_token({
        'access_token': current_user.ssoToken.access_token,
        'expires_in': (current_user.ssoToken.access_token_expires - datetime.utcnow()).total_seconds(),
        'refresh_token': current_user.ssoToken.refresh_token
    })
    client = EsiClient(security)
    invite = {};
    invite['character_id'] = characterID
    invite['role'] = role
    if squadID is not None:
        invite['squad_id'] = squadID
    if wingID is not None:
        invite['wing_id'] = wingID
    response = client.request(api.op['post_fleets_fleet_id_members_invitation'](fleet_id=fleetID, invitation=invite))
    cacheTime = header_to_datetime(response.header['Expires'][0])

    return {'expires': cacheTime, 'data': response.data, 'response': response}
