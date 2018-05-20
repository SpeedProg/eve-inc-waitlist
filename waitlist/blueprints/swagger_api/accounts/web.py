import logging

from flask import Response, make_response, jsonify, request
from flask_login import login_required

from waitlist import db
from waitlist.permissions import perm_manager
from waitlist.storage.database import Account, Character
from waitlist.utility.eve_id_utils import get_character_by_id,\
    get_character_by_name
from waitlist.blueprints.swagger_api.models import errors

from . import bp_v1
from waitlist.signal.signals import send_alt_link_removed, send_alt_link_added
from flask_login.utils import current_user


logger = logging.getLogger(__name__)

perm_manager.define_permission('change_character_links')
perm_change_links = perm_manager.get_permission('change_character_links')


@login_required
@perm_change_links.require()
@bp_v1.route('/<int:account_id>/links/<int:character_id>',
             methods=['DELETE'])
def links_delete_v1(account_id: int, character_id: int) -> Response:
    """
    file: links_delete_v1.yml
    """
    acc: Account = db.session.query(Account).get(account_id)
    if acc is None:
        resp: Response = jsonify(errors.error_404(f'No Account with id {account_id} found.'))
        resp.status_code = 404
        return resp

    character_to_remove: Character = None
    for character in acc.characters:
        if character.id == character_id:
            character_to_remove = character
            break

    if character_to_remove is None:
        resp: Response = jsonify(errors.error_404('No Character link found.'))
        resp.status_code = 404
        return resp
    logger.debug("Trying to delete link from %s to %s", acc, character_to_remove)
    acc.characters.remove(character_to_remove)
    if acc.current_char == character_to_remove.id:
        acc.current_char = None
    db.session.commit()

    # tell handlers about this
    send_alt_link_removed(links_delete_v1, current_user.id, account_id, character_id)

    return make_response('', 204)


@login_required
@perm_change_links.require()
@bp_v1.route('/<int:account_id>/links',
             methods=['POST'])
def links_post_v1(account_id: int) -> Response:
    """
    file: links_post_v1.yml
    """
    data = request.json
    character_name = data['character_name'] if 'character_name' in data else None
    character_id = data['character_id'] if 'character_id' in data else None

    if character_id is not None:
        character_id = int(character_id)

    if character_id is None and character_name is None:
        resp: Response = jsonify(errors.error_400(f"character_name or character_id needs to be provided"))
        resp.status_code = 400
        return resp

    account: Account = db.session.query(Account).get(account_id)

    if account is None:
        resp: Response = jsonify(errors.error_404(f"No Account with id={account_id} exists."))
        resp.status_code = 404
        return resp

    character: Character = None

    if character_id is None:
        character = get_character_by_name(character_name)
    else:
        character = get_character_by_id(character_id)

    if character is None:
        resp: Response = jsonify(errors.error_400(f"No character with "
                                       f"{'id='+character_id if character_id is not None else 'name='+character_name}"))
        resp.status_code = 400
        return resp

    if character in account.characters:
        resp: Response = jsonify(
            errors
                .error_400(f"The Account already has a connection to the "
                           f" with {'id='+character_id if character_id is not None else 'name='+character_name}."))
        resp.status_code = 400
        return resp

    character.owner_hash = ''
    account.characters.append(character)
    db.session.commit()

    send_alt_link_added(links_post_v1, current_user.id, account.id, character.id)

    resp: Response = jsonify({
        'account_id': account.id,
        'character_id': character.id,
        'character_name': character.eve_name
    })
    resp.status_code = 200
    return resp
