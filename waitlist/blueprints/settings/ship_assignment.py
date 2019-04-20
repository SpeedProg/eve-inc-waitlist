import logging
import flask
from flask import Blueprint, Response, render_template
from flask_babel import gettext, lazy_gettext
from flask_login import login_required, current_user
from waitlist.base import db
from waitlist.permissions import perm_manager
from waitlist.storage.database import ShipCheckCollection, WaitlistGroup
from waitlist.blueprints.settings import add_menu_entry

bp = Blueprint('ship_assignment', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('ship_assignment_edit')


@bp.route('/', methods=['GET'])
@login_required
@perm_manager.require('ship_assignment_edit')
def ship_assignments():
    checks = db.session.query(ShipCheckCollection).all()
    wl_groups = db.session.query(WaitlistGroup).all()
    # TODO: this site needs the forms for adding a collection
    # and removing one, only has edit for now
    return render_template('settings/ship_assignment/collection_list.html',
                           checks=checks, groups=wl_groups)

@bp.route('/col/edit', methods=['GET'])
@login_required
@perm_manager.require('ship_assignment_edit')
def collection_edit() -> Response:
    cid: int = int(request.form['collection_id'])
    coll: ShipCheckCollection = db.session.query(ShipCheckCollection).get(cid)
    return render_template('settings/ship_assignment/collection_edit.html', coll=coll)



@bp.route('/col/add', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def collection_add():
    # TODO: Add the collection from data of post
    return redirect(url_for('.ship_assignments'))


@bp.route('/col/remove', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def collection_remove():
    cid: int  = request.form['collection_id']
    db.session.query(ShipCheckCollection).get(cid).delete()
    return redirect(url_for('.ship_assignments'))

@bp.route('/col/add_check')
@login_required
@perm_manager.require('ship_assignment_edit')
def add_checks():
    return render_template('settings/ship_assignment/check')

add_menu_entry('ship_assignment.ship_assignments', lazy_gettext('Ship Classification'), perm_manager.get_permission('ship_assignment_edit').can)
