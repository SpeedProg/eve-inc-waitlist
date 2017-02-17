from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from flask.templating import render_template

from waitlist.permissions import perm_manager
from waitlist.storage.database import CCVote, Account
from waitlist import db
from sqlalchemy.sql.functions import func

bp = Blueprint('settings_ccvote', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('ccvot_viewresults')


@bp.route("/")
@login_required
@perm_manager.require('ccvote_viewresults')
def index():
    fc_results = db.session.query(Account.username, func.count('*')).join(
        CCVote, Account.id == CCVote.fcvoteID
    ).group_by(
        Account.username
    ).order_by(
        func.count('*')
    ).all()
    lm_results = db.session.query(Account.username, func.count('*')).join(
        CCVote, Account.id == CCVote.lmvoteID
    ).group_by(
        Account.username
    ).order_by(
        func.count('*')
    ).all()

    # unique votes
    unique_votes_query_fc = db.session.query(CCVote.voterID.label("voterID"), CCVote.fcvoteID.label("fcvoteID")) \
        .distinct().subquery()
    unique_votes_query_lm = db.session.query(CCVote.voterID.label("voterID"), CCVote.lmvoteID.label("lmvoteID")) \
        .distinct().subquery()

    unqiue_fc_votes = db.session.query(Account.username, func.count('*')) \
        .join(unique_votes_query_fc, unique_votes_query_fc.c.fcvoteID == Account.id
              ).group_by(
        Account.username
    ).order_by(
        func.count('*')
    ).all()
    unqiue_lm_votes = db.session.query(Account.username, func.count('*')) \
        .join(unique_votes_query_lm, unique_votes_query_lm.c.lmvoteID == Account.id
              ).group_by(
        Account.username
    ).order_by(
        func.count('*')
    ).all()
    return render_template("settings/ccvotes.html", fcs=fc_results, lms=lm_results, ufcs=unqiue_fc_votes,
                           ulms=unqiue_lm_votes)
