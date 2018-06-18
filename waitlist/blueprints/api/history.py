
from flask.blueprints import Blueprint
import logging
from waitlist.permissions import perm_manager
from flask_login import login_required
from flask.globals import request
from waitlist import db
from waitlist.storage.database import HistoryEntry, Character, Account
from flask import jsonify
from waitlist.utility.json import make_history_json
from datetime import datetime
bp = Blueprint('api_history', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('comphistory_search')


@bp.route('/comp', methods=['GET'])
@login_required
@perm_manager.require('comphistory_search')
def get_comp_history():
    f_acc_names = request.args.get('accs')
    f_char_names = request.args.get('chars')
    f_start_date = request.args.get('startdate')
    f_start_time = request.args.get('starttime')
    f_end_date = request.args.get('enddate')
    f_end_time = request.args.get('endtime')
    f_actions = request.args.get('actions')

    f_start = None
    f_end = None
    if f_start_date is not None and f_start_time is not None:
        f_start = f_start_date + ' ' + f_start_time

    if f_end_date is not None and f_end_time is not None:
        f_end = f_end_date + ' ' + f_end_time

    query = db.session.query(HistoryEntry)
    if f_acc_names is not None:
        a_names = f_acc_names.split('|')
        condition = None
        for a in a_names:
            if condition is None:
                condition = (Account.username.contains(a))
            else:
                condition = (condition | (Account.username.contains(a)))
        if condition is not None:
            query = query.join(HistoryEntry.source).filter(condition)

    if f_char_names is not None:
        a_names = f_char_names.split('|')
        condition = None
        for a in a_names:
            if condition is None:
                condition = (Character.eve_name.contains(a))
            else:
                condition = (condition | (Character.eve_name.contains(a)))
        if condition is not None:
            query = query.join(HistoryEntry.target).filter(condition)

    if f_start is not None and f_end is not None:
        times = datetime.strptime(f_start[0:16], "%Y-%m-%d %H:%M")
        timee = datetime.strptime(f_end[0:16], "%Y-%m-%d %H:%M")
        query = query.filter((HistoryEntry.time >= times) & (HistoryEntry.time <= timee))

    if f_actions is not None:
        a_actions = f_actions.split('|')
        condition = None
        for a in a_actions:
            if condition is None:
                condition = (HistoryEntry.action == a)
            else:
                condition = (condition | (HistoryEntry.action == a))
        if condition is not None:
            query = query.filter(condition)
    h_entries = query.all()
    history_obj = make_history_json(h_entries)
    json_resp = jsonify(history_obj)
    return json_resp
