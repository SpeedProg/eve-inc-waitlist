from datetime import datetime
from typing import Optional, Tuple

from waitlist.storage.database import APICacheCharacterInfo
from waitlist.utility.outgate.exceptions import check_esi_response
from waitlist.utility.swagger.eve.character import CharacterEndpoint, CharacterInfo
from waitlist.utility.swagger.eve.search import SearchEndpoint, SearchResponse
from waitlist import db
from waitlist.utility.outgate import corporation


def set_from_character_info(self: APICacheCharacterInfo, info: CharacterInfo) -> None:
    self.characterName = info.get_name()
    self.corporationID = info.get_corp_id()
    self.characterBirthday = info.get_birthday()
    self.raceID = info.get_race_id()
    self.expire = info.expires()


def get_character_info(char_id: int, *args) -> APICacheCharacterInfo:
    char_cache: APICacheCharacterInfo = db.session.query(APICacheCharacterInfo) \
        .filter(APICacheCharacterInfo.id == char_id).first()

    if char_cache is None:
        char_cache = APICacheCharacterInfo()
        char_ep = CharacterEndpoint()
        char_info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), get_character_info, args)
        char_cache.id = char_id
        set_from_character_info(char_cache, char_info)
        db.session.add(char_cache)
        db.session.commit()
    elif char_cache.characterName is None:
        char_ep = CharacterEndpoint()
        char_info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), get_character_info, args)
        set_from_character_info(char_cache, char_info)
        db.session.commit()
    else:
        now = datetime.now()
        if char_cache.expire is None or char_cache.expire < now:
            # expired, update it
            char_ep = CharacterEndpoint()
            char_info: CharacterInfo = check_esi_response(char_ep.get_character_info(char_id), get_character_info, args)
            set_from_character_info(char_cache, char_info)
            db.session.commit()

    return char_cache


def get_character_info_by_name(name: str, *args) -> Optional[APICacheCharacterInfo]:
    """
    Get Info for a character by name
    :param name: character name to get the info for
    :return: APICacheCharacterInfo of the character or None if no character with this name can be found
    """
    character = db.session.query(APICacheCharacterInfo).filter(APICacheCharacterInfo.characterName == name).first()

    if character is None:
        search_ep = SearchEndpoint()
        search_info: SearchResponse = check_esi_response(search_ep.public_search(name, ['character']),
                                                         get_character_info_by_name, args)
        if len(search_info.character_ids()) < 1:
            return None
        return get_character_info(search_info.character_ids()[0])
    else:
        # this does expire checks and such for us
        info: APICacheCharacterInfo = get_character_info(character.id)
        # lets make sure with updated info the names still match
        if info.characterName.lower() != name.lower():
            # if they don't, try to find a char for it
            search_ep = SearchEndpoint()
            search_info: SearchResponse = check_esi_response(search_ep.public_search(name, ['character']),
                                                             get_character_info_by_name, args)

            return get_character_info(search_info.character_ids()[0])

        return info


def get_char_or_corp_or_alliance_id_by_name(name: str, *args) -> Optional[int]:
    search_ep = SearchEndpoint()
    search_results: SearchResponse = check_esi_response(
        search_ep.public_search(name, ['character', 'corporation', 'alliance']),
        get_char_or_corp_or_alliance_id_by_name, args)
    ids = search_results.ids(['character', 'corporation', 'alliance'])
    if len(ids) < 1:
        return None
    return ids[0]


def get_char_affiliations(char_id: int, *args) -> Tuple[int, int]:
    """
    Get the id of a characters corporation and alliance
    :param char_id: characters id
    :return: a Tuple[CorpID, AllianceID], alliance could ne None
    """
    char_info = get_character_info(char_id)
    corp_info: corporation.get_info(char_info.corporationID)
    return corp_info.id, corp_info.allianceID

