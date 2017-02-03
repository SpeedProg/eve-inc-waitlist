
from flask.blueprints import Blueprint
import logging
from waitlist.permissions import perm_manager
from flask_login import login_required
from flask.globals import request
from waitlist.base import db
from waitlist.storage.database import HistoryEntry, Character, Account
from flask import jsonify
from waitlist.utility.json import makeHistoryJson
from datetime import datetime
bp = Blueprint('api_history', __name__)
logger = logging.getLogger(__name__)

@bp.route('/comp', methods=['GET'])
@login_required
@perm_manager.require('history_search')
def get_comp_history():
    f_acc_names = request.args.get('accs')
    f_char_names = request.args.get('chars')
    f_time_start = request.args.get('start')
    f_time_end = request.args.get('end')
    f_actions = request.args.get('actions')
    query = db.session.query(HistoryEntry)
    if f_acc_names is not None:
        a_names = f_acc_names.split('|')
        condition = None
        for a in a_names:
            if condition is None:
                condition = (Account.username.contains(a))
            else:
                condition = ((condition) | (Account.username.contains(a)))
        if condition is not None:
            query = query.join(HistoryEntry.source).filter(condition)
    
    if f_char_names is not None:
        a_names = f_char_names.split('|')
        condition = None
        for a in a_names:
            if condition is None:
                condition = (Character.eve_name.contains(a))
            else:
                condition = ((condition) | (Character.eve_name.contains(a)))
        if condition is not None:
            query = query.join(HistoryEntry.target).filter(condition)
    
    if f_time_start is not None and f_time_end is not None:
        times = datetime.strptime(f_time_start, "%Y/%m/%d %H:%M")
        timee = datetime.strptime(f_time_end, "%Y/%m/%d %H:%M")
        query = query.filter((HistoryEntry.time >= times) & (HistoryEntry.time <= timee))
    
    if f_actions is not None:
        a_actions = f_actions.split('|')
        condition = None
        for a in a_actions:
            if condition is None:
                condition = (HistoryEntry.action == a)
            else:
                condition = ((condition) | (HistoryEntry.action == a))
        if condition is not None:
            query = query.filter(condition)
    hEntries = query.all()
    historyObj = makeHistoryJson(hEntries)
    jsonResp = jsonify(historyObj)
    return jsonResp