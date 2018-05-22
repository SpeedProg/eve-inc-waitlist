import logging
from flask.blueprints import Blueprint
from waitlist.permissions import perm_manager
from flask_login import login_required, current_user
from waitlist import db
from waitlist.storage.database import Account, AccountNote
from flask.templating import render_template
import flask
from flask.globals import request
from werkzeug.utils import redirect
from flask.helpers import url_for
from waitlist.utility.constants import account_notes
bp = Blueprint('accounts_profile', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('view_profile')
perm_manager.define_permission('profile_notes_add')
perm_manager.define_permission('view_notes_high')  # <= 500
perm_manager.define_permission('view_notes_low')  # < 100
perm_manager.define_permission('view_notes_med')  # < 200
perm_manager.define_permission('view_notes_all')
perm_manager.define_permission('view_notes')


@bp.route("/<int:accountid>", methods=["GET"])
@login_required
@perm_manager.require('view_profile')
def profile(accountid):
    account = db.session.query(Account).get(accountid)
    if account is None:
        flask.abort(404, "Account not found!")

    max_restriction_level = 0
    if perm_manager.get_permission('view_notes_low').can():
        max_restriction_level = 100
    if perm_manager.get_permission('view_notes_med').can():
        max_restriction_level = 200
    if perm_manager.get_permission('view_notes_high').can():
        max_restriction_level = 500

    criterion = (AccountNote.accountID == accountid)

    if not perm_manager.get_permission("view_notes_all").can():
        criterion = criterion & (AccountNote.restriction_level < max_restriction_level)

    notes = db.session.query(AccountNote).filter(criterion).all()

    return render_template('account/profile.html', account=account, notes=notes)


@bp.route("/byname/<path:username>", methods=["GET"])
@login_required
@perm_manager.require('view_profile')
def profile_by_name(username):
    account = db.session.query(Account).filter(Account.username == username).first()
    if account is None:
        flask.abort(404, "Account not found!")
    
    return profile(account.id)


@bp.route('/<int:accountid>/notes/add', methods=['POST'])
@login_required
@perm_manager.require('profile_notes_add')
def notes_add(accountid):
    note = request.form['note']
    if note is None or note == '':
        flask.abort(400, 'Note can not be empty')

    restriction_level = int(request.form['restriction_level'])
    history_entry = AccountNote(accountID=accountid,
                                byAccountID=current_user.id, note=note,
                                restriction_level=restriction_level,
                                type=account_notes.TYPE_HUMAN)
    db.session.add(history_entry)
    db.session.commit()
    return redirect(url_for('.profile', accountid=accountid))
