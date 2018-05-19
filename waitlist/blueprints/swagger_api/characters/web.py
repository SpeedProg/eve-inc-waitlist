from flask import Response, request, make_response, jsonify
from flask_login import login_required

from waitlist import db
from waitlist.blueprints.swagger_api.characters import bp_v1
from waitlist.blueprints.swagger_api.models import errors
from waitlist.permissions import perm_manager
from waitlist.storage.database import Character

perm_manager.define_permission('change_character_data')
perm_change_character_data = perm_manager.get_permission('change_character_data')


@login_required
@perm_change_character_data.require()
@bp_v1.route('/<int:character_id>/',
             methods=['PUT'])
def character_put_v1(character_id: int) -> Response:
    """
    file: character_put_v1.yml
    """
    owner_hash = request.form.get('owner_hash')
    character: Character = db.session.query(Character).get(character_id)
    if character is None:
        resp: Response = jsonify(errors.error_404(f'Character with id={character_id} does not exist.'))
        resp.status_code = 404
        return resp

    character.owner_hash = owner_hash
    db.session.commit()
    return make_response('', 204)
