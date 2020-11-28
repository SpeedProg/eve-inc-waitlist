from flask_login.utils import login_required, current_user
from waitlist.base import app, db
from flask.templating import render_template
from flask.globals import request
from waitlist.storage.database import WaitlistGroup, CalendarEvent, TriviaAnswer, Trivia, WaitlistEntry
from typing import Optional, Sequence
from datetime import datetime
from waitlist.utility.coms import get_connector
from waitlist.utility.config import stattool_enabled, stattool_uri, stattool_sri

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

    trivias: Optional[Sequence[TriviaAnswer]] = db.session.query(Trivia)\
        .filter((Trivia.fromTime <= datetime.utcnow()) & (Trivia.toTime > datetime.utcnow())).all()
    if trivias is None:
        trivias = []

    com_connector = get_connector()
    coms = None if com_connector is None else com_connector.get_connect_display_info()
    is_on_waitlist = db.session.query(WaitlistEntry).filter(WaitlistEntry.user == current_user.get_eve_id()).first() is not None

    return render_template("index.html", lists=wlists, user=current_user, is_index=True, is_on_wl=is_on_waitlist,
                           newbro=new_bro, group=group, groups=activegroups, coms=coms, events=events,
                           trivias=trivias, ccvote_on=cc_vote_on,
                           stattool_enabled=stattool_enabled, stattool_uri=stattool_uri, stattool_sri=stattool_sri)
