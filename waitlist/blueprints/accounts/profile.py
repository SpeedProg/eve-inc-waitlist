import logging
from flask.blueprints import Blueprint
from waitlist.permissions import perm_manager
from flask_login import login_required
from waitlist.base import db
from waitlist.storage.database import Account, RoleHistoryEntry
from flask.templating import render_template
import flask
bp = Blueprint('accounts_profile', __name__)
logger = logging.getLogger(__name__)

@bp.route("/<int:accountid>", methods=["GET"])
@login_required
@perm_manager.require('commandcore')
def profile(accountid):
    account = db.session.query(Account).get(accountid)
    if (account == None):
        flask.abort(404, "Account not found!")
    notes = None
    if perm_manager.getPermission("officer").can():
        notes = db.session.query(RoleHistoryEntry).filter(RoleHistoryEntry.accountID == accountid).all();
    return render_template('account/profile.html', account=account, notes=notes)

@bp.route("/<path:username>", methods=["GET"])
@login_required
@perm_manager.require('commandcore')
def profile_by_name(username):
    account = db.session.query(Account).filter(Account.username == username).first()
    if (account == None):
        flask.abort(404, "Account not found!")
    notes = None
    if perm_manager.getPermission('council').can():
        notes = db.session.query(RoleHistoryEntry).filter(RoleHistoryEntry.accountID == account.id).all();
    return render_template('account/profile.html', account=account, notes=notes)