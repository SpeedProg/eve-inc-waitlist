
from flask.views import MethodView
from flask.blueprints import Blueprint
import logging
from waitlist.base import db, limiter
from waitlist.storage.database import WaitlistGroup, Waitlist
from flask import jsonify
from waitlist.utility.json import makeJsonGroups, makeJsonGroup, makeJsonWaitlistsBaseData,\
 makeJsonWaitlistBaseData
from click.decorators import group
import flask
from flask_login import current_user
from flask.globals import request
from flask_limiter.util import get_ipaddr
from urllib.parse import urlencode

bp = Blueprint('api_waitlists', __name__)
logger = logging.getLogger(__name__)

def get_ratekey_func_with_arguments(arglist):
    def ratekeyfunc():
        addr = get_ipaddr();
        params = {}
        for argname in arglist:
            params[argname] = str(request.view_args[argname])
            
        # we need to encode the url properly instead of just doing &name=value...
        # so some one can't insert stuff to make the request unique
        key = addr + urlencode(params)
        return key
    return ratekeyfunc

class WaitlistGroupsAPI(MethodView):
    decorators = [
        limiter.limit("1/minute", key_func=get_ratekey_func_with_arguments(['groupID']), exempt_when=lambda: current_user.is_authenticated),
        limiter.limit("5/minute", exempt_when=lambda: current_user.is_authenticated)
    ]
    def get(self, groupID):
        if groupID is None:
            groups = db.session.query(WaitlistGroup).all();
            return jsonify(makeJsonGroups(groups))
        else:
            group = db.session.query(WaitlistGroup).get(groupID)
            if group is None:
                flask.abort(404, "No such group")
            return jsonify(makeJsonGroup(group))

class WaitlistBaseDataAPI(MethodView):
    decorators = [
        limiter.limit("1/minute", key_func=get_ratekey_func_with_arguments(['waitlistID']), exempt_when=lambda: current_user.is_authenticated),
        limiter.limit("5/minute", exempt_when=lambda: current_user.is_authenticated)
    ]
    def get(self, waitlistID):
        if waitlistID is None:
            waitlists = db.session.query(Waitlist).all();
            return jsonify(makeJsonWaitlistsBaseData(waitlists))
        else:
            waitlist = db.session.query(Waitlist).get(waitlistID)
            if waitlist is None:
                flask.abort(404, "No such waitlist")
            if waitlistID is None:
                flask.abort(404, 'No Waitlist with this ID found')
            return jsonify(makeJsonWaitlistBaseData(waitlist))
        
groups_view = WaitlistGroupsAPI.as_view('groups')
waitlist_base_view = WaitlistBaseDataAPI.as_view('wlbasedata')

bp.add_url_rule(rule='/groups/', defaults={'groupID': None}, view_func=groups_view, methods=['GET'])
bp.add_url_rule(rule='/groups/<int:groupID>', view_func=groups_view, methods=['GET'])

bp.add_url_rule(rule='/waitlists/', defaults={'waitlistID': None}, view_func=waitlist_base_view, methods=['GET'])
bp.add_url_rule(rule='/waitlists/<int:waitlistID>', view_func=waitlist_base_view, methods=['GET'])
