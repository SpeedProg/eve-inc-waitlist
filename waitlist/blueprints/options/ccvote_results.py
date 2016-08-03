from flask.blueprints import Blueprint
import logging
from flask_login import login_required
from waitlist.data.perm import perm_leadership
from flask.templating import render_template
from waitlist.storage.database import CCVote, Account, Character
from waitlist.base import db
from sqlalchemy.sql.functions import func
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
    
    # unique votes
    unique_votes_query_fc = db.session.query(CCVote.voterID.label("voterID"), CCVote.fcvoteID.label("fcvoteID")).distinct().subquery()
    unique_votes_query_lm = db.session.query(CCVote.voterID.label("voterID"), CCVote.lmvoteID.label("lmvoteID")).distinct().subquery()
    
    unqiueFCVotes = db.session.query(Account.username, func.count('*')
        ).join(unique_votes_query_fc, unique_votes_query_fc.c.fcvoteID==Account.id
        ).group_by(
                   Account.username
        ).order_by(
                   func.count('*')
        ).all()
    unqiueLMVotes = db.session.query(Account.username, func.count('*')
        ).join(unique_votes_query_lm, unique_votes_query_lm.c.lmvoteID==Account.id
        ).group_by(
                   Account.username
        ).order_by(
                   func.count('*')
        ).all()
    return render_template("settings/ccvotes.html", fcs=fcResults, lms=lmResults, ufcs=unqiueFCVotes, ulms=unqiueLMVotes)