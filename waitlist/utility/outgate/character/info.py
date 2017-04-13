from datetime import datetime
from typing import Optional, Tuple

from storage.database import APICacheCharacterInfo
from utility.swagger.eve.character import CharacterEndpoint
from utility.swagger.eve.search import SearchEndpoint
from waitlist import db
from waitlist.utility.outgate import corporation


def get_character_info(char_id: int) -> APICacheCharacterInfo:
    char_cache: APICacheCharacterInfo = db.session.query(APICacheCharacterInfo) \
        .filter(APICacheCharacterInfo.id == char_id).first()

    if char_cache is None:
        char_cache = APICacheCharacterInfo()
        char_ep = CharacterEndpoint()
        char_info = char_ep.get_character_info(char_id)
        char_cache.set_from_character_info(char_info)
        db.session.add(char_cache)
        db.session.commit()
    elif char_cache.characterName is None:
        char_ep = CharacterEndpoint()
        char_info = char_ep.get_character_info(char_id)
        char_cache.set_from_character_info(char_info)
        db.session.commit()
    else:
        now = datetime.now()
        if char_cache.expire is None or char_cache.expire < now:
            # expired, update it
            char_ep = CharacterEndpoint()
            char_info = char_ep.get_character_info(char_id)
            char_cache.set_from_character_info(char_info)
            db.session.commit()

    return char_cache


def get_character_info_by_name(name: str) -> Optional[APICacheCharacterInfo]:
    """
    Get Info for a character by name
    :param name: character name to get the info for
    :return: APICacheCharacterInfo of the character or None if no character with this name can be found
    """
    character = db.session.query(APICacheCharacterInfo).filter(APICacheCharacterInfo.name == name).first()

    if character is None:
        search_ep = SearchEndpoint()
        search_info = search_ep.public_search(name, ['character'])
        if search_info is None:
            return None
        return get_character_info(search_info.character_ids()[0])
    else:
        # this does expire checks and such for us
        info: APICacheCharacterInfo = get_character_info(character.id)
        # lets make sure with updated info the names still match
        if info.characterName.lower() != name.lower():
            # if they don't, try to find a char for it
            search_ep = SearchEndpoint()
            search_info = search_ep.public_search(name, ['character'])
            if search_info is None:
                return None
            return get_character_info(search_info.character_ids()[0])

        return info


def get_char_or_corp_or_alliance_id_by_name(name: str) -> Optional[int]:
    search_ep = SearchEndpoint()
    search_results = search_ep.public_search(name, ['character', 'corporation', 'alliance'])
    ids = search_results.ids(['character', 'corporation', 'alliance'])
    if len(ids) < 1:
        return None
    return ids[0]


def get_char_affiliations(char_id: int) -> Tuple[int, int]:
    """
    Get the id of a characters corporation and alliance
    :param char_id: characters id
    :return: a Tuple[CorpID, AllianceID], alliance could ne None
    """
    char_info = get_character_info(char_id)
    corp_info = corporation.get_info(char_info.corporationID)
    return corp_info.id, corp_info.allianceID

