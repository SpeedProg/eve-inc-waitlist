from datetime import datetime, time, timedelta
from flask.blueprints import Blueprint
import logging
from flask.templating import render_template
from flask_login import login_required, current_user
from flask.globals import request
import flask
from werkzeug.utils import redirect
from flask.helpers import url_for
from waitlist.base import db
from waitlist.storage.database import Account, CCVote, Role
from sqlalchemy.sql.expression import asc
from flask_babel import gettext

bp = Blueprint('cc_vote', __name__)
logger = logging.getLogger(__name__)

endTime = datetime(2016, 8, 7, 11, 0, 0)
startTime = datetime(2016, 7, 4, 11, 0, 0)


@bp.route("/", methods=["GET"])
@login_required
def index():
    current_time = datetime.utcnow()
    if current_time < startTime or current_time > endTime:
        flask.abort(404, "Voting period is from %s to %s and is over or did not start yet" % (startTime, endTime))
    if current_user.type != "character":
        flask.abort(403, "For voting you need to be on a normal linemember login," +
                    " please log out and use the linemember auth.")
    if has_voted_today(current_user.get_eve_id()):
        flask.abort(403, "You already voted during this Eve-Day, you can vote again after Downtime!")
    # noinspection PyPep8
    active_fc_accounts = db.session.query(Account).join(Account.roles).filter(
        ((Role.name == 'fc') | (Role.name == 'tbadge'))
        & (Account.disabled == False)).order_by(asc(Account.username)).all()
    # noinspection PyPep8
    active_lm_accounts = db.session.query(Account).join(Account.roles).filter(
        ((Role.name == 'lm') | (Role.name == 'rbadge'))
        & (Account.disabled == False)).order_by(asc(Account.username)).all()
    return render_template("waitlist/ccvote.html", fcs=active_fc_accounts, lms=active_lm_accounts)


@bp.route("/", methods=["POST"])
@login_required
def submit():
    current_time = datetime.utcnow()
    if current_time < startTime or current_time > endTime:
        flask.abort(404, "Voting period is from %s to %s and is over or did not start yet" % (startTime, endTime))
    if current_user.type != "character":
        flask.abort(403, "For voting you need to be on a normal linemember login," +
                    " please log out and use the linemember auth.")
    fc_vote = int(request.form.get('fc-vote'))
    lm_vote = int(request.form.get('lm-vote'))

    if has_voted_today(current_user.get_eve_id()):
        flask.abort(500, "You already voted today!")

    if (not is_fc(fc_vote)) or (not is_lm(lm_vote)):
        flask.abort("Either the FC you voted for is not an FC or the LM you voted for is not an LM!")
    logger.info("%s is voting for fc=%d and lm=%d", current_user.get_eve_name(), fc_vote, lm_vote)
    if fc_vote == -1:
        fc_vote = None
    if lm_vote == -1:
        lm_vote = None
    add_vote(current_user.get_eve_id(), fc_vote, lm_vote)
    flask.flash(gettext("Thank you for voting, you can vote again after the next eve downtime!"), "success")
    return redirect(url_for('index'))


def add_vote(voter_id, fc_id, lm_id):
    vote = CCVote(voterID=voter_id, lmvoteID=lm_id, fcvoteID=fc_id, time=datetime.utcnow())
    db.session.add(vote)
    db.session.commit()


def is_fc(account_id):
    if account_id == -1:
        return True
    account = db.session.query(Account).filter(Account.id == account_id).one()
    for role in account.roles:
        if role.name == 'fc' or role.name == 'tbadge':
            return True
    return False


def is_lm(account_id):
    if account_id == -1:
        return True
    account = db.session.query(Account).filter(Account.id == account_id).one()
    for role in account.roles:
        if role.name == 'lm' or role.name == 'rbadge':
            return True
    return False


def has_voted_today(eve_id):
    lastdaystart = get_serverday_start()
    lastvote = db.session.query(CCVote).filter((CCVote.voterID == eve_id) & (CCVote.time > lastdaystart)).first()
    return lastvote is not None


def get_serverday_start():
    utc_current = datetime.utcnow()
    today = utc_current.date()
    c_time = utc_current.time()
    # if we are over 11:00:00 we need the current day, else we need the previous day
    if c_time < time(11, 0, 0):
        today = today - timedelta(1)
    return datetime.combine(today, time(11, 0, 0))
