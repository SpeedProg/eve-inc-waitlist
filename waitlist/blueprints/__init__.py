from datetime import datetime
from typing import Sequence, Optional

import flask
import logging

from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_principal import identity_changed, Identity, AnonymousIdentity
from flask_login import login_required, current_user, login_user, logout_user

from waitlist.utility import config
from waitlist.utility.config import stattool_enabled, stattool_uri,\
    stattool_sri, disable_teamspeak

from waitlist.base import app, db
from waitlist.storage.database import WaitlistGroup, TeamspeakDatum, CalendarEvent, WaitlistEntry, Account, Trivia

from flask_babel import _, lazy_gettext
from flask.helpers import flash
from waitlist.utility.coms import get_connector

logger = logging.getLogger(__name__)


def is_on_wl():
    eve_id = current_user.get_eve_id()
    entry = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == eve_id).first()
    return entry is not None


@app.route('/', methods=['GET'])
@login_required
def index():
    """
    current_time: datetime = datetime.utcnow()
    end_time: datetime = datetime(2016, 8, 7, 11, 0, 0)
    start_time: datetime = datetime(2016, 7, 4, 11, 0, 0)
    cc_vote_on: bool = ((start_time < current_time) and (current_time < end_time))
    """
    cc_vote_on: bool = False

    if 'groupId' in request.args:
        group_id = int(request.args.get('groupId'))
        group = db.session.query(WaitlistGroup).get(group_id)
    else:
        # noinspection PyPep8
        group = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).order_by(
            WaitlistGroup.ordering).first()

    if group is None:
        return render_template("index.html", is_index=True, ccvote_on=cc_vote_on)

    new_bro = current_user.is_new

    wlists = [l for l in group.waitlists]

    # noinspection PyPep8
    activegroups = db.session.query(WaitlistGroup).filter(WaitlistGroup.enabled == True).all()

    events = db.session.query(CalendarEvent).filter(CalendarEvent.eventTime > datetime.utcnow()).order_by(
        CalendarEvent.eventTime.asc()).limit(10).all()

    trivias: Optional[Sequence[Trivia]] = db.session.query(Trivia)\
        .filter((Trivia.fromTime <= datetime.utcnow()) & (Trivia.toTime > datetime.utcnow())).all()
    if trivias is None:
        trivias = []

    com_connector = get_connector()
    coms = None if com_connector is None else com_connector.get_connect_display_info()
    return render_template("index.html", lists=wlists, user=current_user, is_index=True, is_on_wl=is_on_wl(),
                           newbro=new_bro, group=group, groups=activegroups, coms=coms, events=events,
                           trivias=trivias, ccvote_on=cc_vote_on,
                           stattool_enabled=stattool_enabled, stattool_uri=stattool_uri, stattool_sri=stattool_sri)


@app.route("/help", methods=["GET"])
def site_help():
    return render_template("help.html")


@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


# callable like /tokenauth?token=359th8342rt0f3uwf0234r
@app.route('/tokenauth')
def login_token():
    if not config.debug_enabled:
        flask.abort(404, _("Tokens where removed, please use the EVE SSO"))
        return

    token = request.args.get('token')
    user = db.session.query(Account).filter(Account.login_token == token).first()

    # token was not found
    if user is None:
        return flask.abort(401)

    if user.disabled:
        return flask.abort(403)

    logger.info("Got User %s", user)
    login_user(user)
    logger.info("Logged in User %s", user)

    # notify principal extension
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))

    return redirect(url_for('index'), code=303)


@app.route('/logout')
@login_required
def logout():
    logout_user()

    for key in ('identity.name', 'identity.auth_type'):
        flask.globals.session.pop(key, None)

    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())

    return render_template("logout.html")
