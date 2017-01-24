import logging
from flask.blueprints import Blueprint
from waitlist.permissions import perm_manager
from flask_login import login_required, current_user
from waitlist.base import db
from waitlist.storage.database import Account, RoleHistoryEntry
from flask.templating import render_template
import flask
from flask.globals import request
from werkzeug.utils import redirect
from flask.helpers import url_for
bp = Blueprint('accounts_profile', __name__)
logger = logging.getLogger(__name__)

@bp.route("/<int:accountid>", methods=["GET"])
@login_required
@perm_manager.require('view_profile')
def profile(accountid):
    account = db.session.query(Account).get(accountid)
    if (account == None):
        flask.abort(404, "Account not found!")
    notes = None
    if perm_manager.getPermission("officer").can():
        notes = db.session.query(RoleHistoryEntry).filter(RoleHistoryEntry.accountID == accountid).all();
    return render_template('account/profile.html', account=account, notes=notes)

@bp.route("/byname/<path:username>", methods=["GET"])
@login_required
@perm_manager.require('view_profile')
def profile_by_name(username):
    account = db.session.query(Account).filter(Account.username == username).first()
    if (account == None):
        flask.abort(404, "Account not found!")
    notes = None
    if perm_manager.getPermission('view_notes').can():
        notes = db.session.query(RoleHistoryEntry).filter(RoleHistoryEntry.accountID == account.id).all();
    return render_template('account/profile.html', account=account, notes=notes)

@bp.route('/<int:accountid>/notes/add', methods=['POST'])
@login_required
@perm_manager.require('add_notes')
def notes_add(accountid):
    note = request.form['note']
    restriction_level = int(request.form['restriction_level'])
    historyEntry = RoleHistoryEntry(accountID=accountid, byAccountID=current_user.id, note=note, restriction_level=restriction_level)
    db.session.add(historyEntry)
    db.session.commit()
    return redirect(url_for('.profile', accountid=accountid))