from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist.data.perm import perm_leadership
from flask.templating import render_template
from waitlist.storage.database import CCVote, Account
from waitlist.base import db
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.selectable import alias
bp = Blueprint('settings_ccvote', __name__)
logger = logging.getLogger(__name__)

@bp.route("/")
@login_required
@perm_leadership.require()
def index():
    fcResults = db.session.query(Account.username, func.count('*')).join(
        CCVote, Account.id==CCVote.fcvoteID
        ).group_by(
                   Account.username
        ).order_by(
                   func.count('*')
        ).all()
    lmResults = db.session.query(Account.username, func.count('*')).join(
        CCVote, Account.id==CCVote.lmvoteID
        ).group_by(
                   Account.username
        ).order_by(
                   func.count('*')
        ).all()
    return render_template("settings/ccvotes.html", fcs=fcResults, lms=lmResults)