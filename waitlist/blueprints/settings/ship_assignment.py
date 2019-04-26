import logging
from typing import Any
from decimal import Decimal
import flask
from flask import Blueprint, Response, render_template, request,\
    url_for, redirect
from flask_babel import gettext, lazy_gettext
from flask_login import login_required, current_user
from waitlist.base import db
from waitlist.permissions import perm_manager
from waitlist.storage.database import ShipCheckCollection, WaitlistGroup, ShipCheck,\
    InvType, InvGroup, MarketGroup
from waitlist.blueprints.settings import add_menu_entry
from waitlist.utility.constants import check_types

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
    cid: int = int(request.args.get('collection_id'))
    coll: ShipCheckCollection = db.session.query(ShipCheckCollection).get(cid)
    groups: WaitlistGroup = db.session.query(WaitlistGroup).all()
    return render_template('settings/ship_assignment/collection_edit.html', coll=coll, groups=groups, check_type_map=check_types.CHECK_NAME_MAP)


@bp.route('/col/<int:coll_id>/change', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def collection_change(coll_id: int) -> Response:
    coll_name = request.form['coll_name']
    group_id = request.form['group_id']
    target_id = request.form['target_id']
    tag = request.form['tag']
    collection: ShipCheckCollection = db.session.query(ShipCheckCollection).get(coll_id)
    if collection is None:
        flask.flash('Invalid Collection ID provided', 'danger')
        return redirect(url_for('.ship_assignments'))

    collection.checkCollectionName = coll_name
    collection.waitlistGroupID = group_id
    collection.defaultTargetID = target_id
    collection.defaultTag = tag
    db.session.commit()
    flask.flash('Collection was updated', 'success')
    return redirect(url_for('.collection_edit', collection_id=coll_id))


@bp.route('/col/add', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def collection_add():
    name: str = request.form['name']
    wl_group_id = int(request.form['group_id'])
    def_target_id = int(request.form['target_id'])
    tag = request.form['tag']

    collection = ShipCheckCollection(
        checkCollectionName=name,
        waitlistGroupID=wl_group_id,
        defaultTargetID=def_target_id,
        defaultTag=tag
    )
    db.session.add(collection)
    db.session.commit()
    return redirect(url_for('.ship_assignments'))


@bp.route('/col/remove', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def collection_remove():
    cid: int  = request.form['collection_id']
    db.session.query(ShipCheckCollection).filter(ShipCheckCollection.checkCollectionID == cid).delete()
    db.session.commit()
    return redirect(url_for('.ship_assignments'))


def get_id_type(check_type: int) -> Any:
    type_mapping: Dict[int, Any] = {
        check_types.SHIP_CHECK_TYPEID: InvType,
        check_types.SHIP_CHECK_INVGROUP: InvGroup,
        check_types.SHIP_CHECK_MARKETGROUP: MarketGroup,
        check_types.MODULE_CHECK_TYPEID: InvType,
        check_types.MODULE_CHECK_MARKETGROUP: MarketGroup
    }
    return type_mapping[check_type]


@bp.route('/col/<int:coll_id>/checks', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def check_add(coll_id: int) -> Response:
    collection: ShipCheckCollection = db.session.query(ShipCheckCollection).get(coll_id)
    name: str = request.form['check_name']
    check_id: int = int(request.form['check_type'], 10)
    target: int  = int(request.form['check_target'], 10)
    order: int = int(request.form['order'], 10)
    modifier: Decimal = Decimal(request.form['modifier'])
    check_ids = [int(check_id.strip()) for check_id in request.form['ids'].split(',')]
    tag = request.form['tag']

    check: ShipCheck = ShipCheck(
        checkName=name,
        collectionID=coll_id,
        checkTargetID=target,
        checkType=check_id,
        order=order,
        modifier=modifier,
        checkTag=tag
    )

    target_type = get_id_type(check_id)

    for obj_id in check_ids:
        obj = db.session.query(target_type).get(obj_id)
        check.ids.append(obj)

    # we only have restrictions for specific types of checks
    if check_id in [check_types.MODULE_CHECK_MARKETGROUP, check_types.MODULE_CHECK_TYPEID]:
        rest_typeids = [int(i.strip()) for i in request.form['rest_typeids'].split(',')]
        rest_invgroupids = [int(i.strip()) for i in request.form['rest_invgroupids'].split(',')]
        rest_mgroupids = [int(i.strip()) for i in request.form['rest_mgroupids'].split(',')]

        for type_id in rest_typeids:
            invtype = db.session.query(InvType).get(type_id)
            check.check_rest_types.append(invtype)
        for group_id in rest_invgroupids:
            check.check_rest_groups.append(
                db.session.query(InvGroup).get(group_id)
            )
        for mgroup_id in rest_mgroupids:
            check.check_rest_market_groups.append(
                db.session.query(MarketGroup).get(mgroup_id)
            )


    db.session.add(check)
    db.session.commit()

    return redirect(url_for('.collection_edit', collection_id=coll_id))


@bp.route('/check/<int:check_id>/edit', methods=['GET'])
@login_required
@perm_manager.require('ship_assignment_edit')
def check_edit(check_id:int) -> Response:
    check: ShipCheck = db.session.query(ShipCheck).get(check_id)
    return render_template('settings/ship_assignment/check_edit.html', check=check,
                           check_type_map=check_types.CHECK_NAME_MAP,
                           waitlists=check.collection.waitlistGroup.waitlists)



@bp.route('/check/<int:check_id>/', methods=['POST'])
@login_required
@perm_manager.require('ship_assignment_edit')
def check_change(check_id:int) -> Response:
    name: str = request.form['check_name']
    order: int = int(request.form['order'])
    target_id: int = int(request.form['check_target'])
    check_modifier: Decimal = Decimal(request.form['modifier'])
    check_type: int = int(request.form['check_type'])
    check_ids = [int(check_id.strip()) for check_id in request.form['ids'].split(',')]
    tag = request.form['tag']

    check: ShipCheck = db.session.query(ShipCheck).get(check_id)
    # clear old items
    # this needs to be done before changing the type
    # because otherwise we delete from the wrong relationship
    check.ids=[]


    check.order = order
    check.checkTargetID = target_id
    check.checkType = check_type
    check.checkName = name
    check.modifier = check_modifier
    check.tag = tag
    # add new items
    # this needs to be done after changing the type
    # because otherwise we add to the wrong relationship
    target_type = get_id_type(check_type)
    for obj_id in check_ids:
        obj = db.session.query(target_type).get(obj_id)
        check.ids.append(obj)

    # we only have restrictions for specific types of checks
    if check_type in [check_types.MODULE_CHECK_MARKETGROUP, check_types.MODULE_CHECK_TYPEID]:
        logger.debug("Adding restrictions to check")
        rest_typeids = [int(i.strip()) for i in request.form['rest_typeids'].split(',') if i.strip()]
        rest_invgroupids = [int(i.strip()) for i in request.form['rest_invgroupids'].split(',') if i.strip()]
        rest_mgroupids = [int(i.strip()) for i in request.form['rest_mgroupids'].split(',') if i.strip()]
        logger.debug("types: %r invgroups: %r mgroups: %r", rest_typeids, rest_invgroupids, rest_mgroupids)
        check.check_rest_types = []
        check.check_rest_groups = []
        check.check_rest_market_groups = []
        for type_id in rest_typeids:
            invtype = db.session.query(InvType).get(type_id)
            check.check_rest_types.append(invtype)
        for group_id in rest_invgroupids:
            check.check_rest_groups.append(
                db.session.query(InvGroup).get(group_id)
            )
        for mgroup_id in rest_mgroupids:
            check.check_rest_market_groups.append(
                db.session.query(MarketGroup).get(mgroup_id)
            )

    db.session.commit()
    return redirect(url_for('.collection_edit', collection_id=check.collection.checkCollectionID))


add_menu_entry('ship_assignment.ship_assignments', lazy_gettext('Ship Classification'), perm_manager.get_permission('ship_assignment_edit').can)
