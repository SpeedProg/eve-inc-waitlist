
from flask.views import MethodView
from flask.blueprints import Blueprint
import logging
from waitlist.base import db, limiter
from waitlist.storage.database import WaitlistGroup, Waitlist
from flask import jsonify
from waitlist.utility.json import make_json_groups, make_json_group, make_json_waitlists_base_data,\
 make_json_waitlist_base_data
from waitlist.utility.config import disable_public_api
import flask
from flask_login import current_user, login_required
from flask.globals import request
from flask_limiter.util import get_ipaddr
from urllib.parse import urlencode

bp = Blueprint('api_waitlists', __name__)
logger = logging.getLogger(__name__)


def api_login_required(f):
    """If we require login apply the check"""
    if disable_public_api:
        return login_required(f)
    return f


def get_ratekey_func_with_arguments(arglist):
    def ratekeyfunc():
        addr = get_ipaddr()
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
        limiter.limit("1/minute", key_func=get_ratekey_func_with_arguments(['group_id']),
                      exempt_when=lambda: current_user.is_authenticated),
        limiter.limit("5/minute", exempt_when=lambda: current_user.is_authenticated),
        api_login_required
    ]

    @classmethod
    def get(cls, group_id):
        if group_id is None:
            groups = db.session.query(WaitlistGroup).all()
            return jsonify(make_json_groups(groups))
        else:
            group = db.session.query(WaitlistGroup).get(group_id)
            if group is None:
                flask.abort(404, "No such group")
            return jsonify(make_json_group(group))


class WaitlistBaseDataAPI(MethodView):
    decorators = [
        limiter.limit("1/minute", key_func=get_ratekey_func_with_arguments(['waitlist_id']),
                      exempt_when=lambda: current_user.is_authenticated),
        limiter.limit("5/minute", exempt_when=lambda: current_user.is_authenticated),
        api_login_required
    ]

    @classmethod
    def get(cls, waitlist_id):
        if waitlist_id is None:
            waitlists = db.session.query(Waitlist).all()
            return jsonify(make_json_waitlists_base_data(waitlists))
        else:
            waitlist = db.session.query(Waitlist).get(waitlist_id)
            if waitlist is None:
                flask.abort(404, "No such waitlist")
            if waitlist_id is None:
                flask.abort(404, 'No Waitlist with this ID found')
            return jsonify(make_json_waitlist_base_data(waitlist))


groups_view = WaitlistGroupsAPI.as_view('groups')
waitlist_base_view = WaitlistBaseDataAPI.as_view('wlbasedata')

bp.add_url_rule(rule='/groups/', defaults={'group_id': None}, view_func=groups_view, methods=['GET'])
bp.add_url_rule(rule='/groups/<int:group_id>', view_func=groups_view, methods=['GET'])

bp.add_url_rule(rule='/waitlists/', defaults={'waitlist_id': None}, view_func=waitlist_base_view, methods=['GET'])
bp.add_url_rule(rule='/waitlists/<int:waitlist_id>', view_func=waitlist_base_view, methods=['GET'])
