from __future__ import absolute_import
from flask.views import MethodView
from flask.blueprints import Blueprint
import logging
from waitlist.base import db
from waitlist.storage.database import WaitlistGroup, Waitlist
from flask import jsonify
from waitlist.utility.json import makeJsonGroups, makeJsonGroup, makeJsonWaitlistsBaseData,\
 makeJsonWaitlistBaseData
from click.decorators import group
import flask

bp = Blueprint('api_waitlists', __name__)
logger = logging.getLogger(__name__)

class WaitlistGroupsAPI(MethodView):
    def get(self, groupID):
        if groupID is None:
            groups = db.session.query(WaitlistGroup).all();
            return jsonify(makeJsonGroups(groups))
        else:
            group = db.session.query(WaitlistGroup).get(groupID)
            return jsonify(makeJsonGroup(group))

class WaitlistBaseDataAPI(MethodView):
    def get(self, waitlistID):
        if waitlistID is None:
            waitlists = db.session.query(Waitlist).all();
            return jsonify(makeJsonWaitlistsBaseData(waitlists))
        else:
            waitlist = db.session.query(Waitlist).get(waitlistID)
            if waitlistID is None:
                flask.abort(404, 'No Waitlist with this ID found')
            return jsonify(makeJsonWaitlistBaseData(waitlist))
        
groups_view = WaitlistGroupsAPI.as_view('groups')
waitlist_base_view = WaitlistBaseDataAPI.as_view('wlbasedata')

bp.add_url_rule(rule='/groups/', defaults={'groupID': None}, view_func=groups_view, methods=['GET'])
bp.add_url_rule(rule='/groups/<int:groupID>', view_func=groups_view, methods=['GET'])

bp.add_url_rule(rule='/waitlists/', defaults={'waitlistID': None}, view_func=waitlist_base_view, methods=['GET'])
bp.add_url_rule(rule='/waitlists/<int:waitlistID>', view_func=waitlist_base_view, methods=['GET'])
