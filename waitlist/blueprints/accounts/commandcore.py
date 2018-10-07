import logging
from flask.blueprints import Blueprint

from waitlist.blueprints.settings.accounts import clean_alt_list
from waitlist.permissions import perm_manager
from flask_login import login_required
from waitlist import db
from waitlist.storage.database import Account, Role
from flask.templating import render_template

bp = Blueprint('accounts_cc', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('commandcore')


@bp.route("/", methods=["GET"])
@login_required
@perm_manager.require('commandcore')
def accounts():
    clean_alt_list()

    # noinspection PyPep8
    accs = db.session.query(Account).\
        filter(Account.disabled == False).\
        order_by(Account.username).all()
    roles = db.session.query(Role).all()
    return render_template("waitlist/tools/commandcore_list.html", accounts=accs, roles=roles)
