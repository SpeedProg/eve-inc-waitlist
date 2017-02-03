import logging
import string
from datetime import datetime
from typing import List, Sequence

from flask import Blueprint
from flask import render_template
from flask.globals import request
from flask_login import login_required, current_user
from sqlalchemy import or_

from waitlist.base import db
from waitlist.permissions import perm_manager
from waitlist.storage.database import Account, CalendarEvent, CalendarEventCategory

bp = Blueprint('calendar', __name__)
logger = logging.getLogger(__name__)

@bp.route("/", methods=['GET'])
@login_required
@perm_manager.require('commandcore')
def get_index():
    accounts: Sequence[Account] = db.session.query(Account).filter(Account.disabled == False).all()

    event_query = db.session.query(CalendarEvent).filter(CalendarEvent.eventTime > datetime.utcnow())
    if not perm_manager.getPermission('calendar_event_see_all').can():
        event_query = event_query.filter(CalendarEvent.eventCreatorID == current_user.id)

    event_query.order_by(CalendarEvent.eventTime.asc())
    events = event_query.all()

    return render_template('calendar/settings.html', accounts=accounts, events=events)



@bp.route("/", methods=['POST'])
@login_required
@perm_manager.require('commandcore')
def post_index():
    category_id: int = int(request.form['categoryID'])
    backseats_string: List[string] = request.form.getlist['backseats']
    backseat_ids: List[int] = []
    for backseat_string in backseats_string:
        backseat_ids.append(int(backseat_string))

    event_time: datetime = datetime.strptime(request.form['time'], "%Y/%m/%d %H:%M")

    category: CalendarEventCategory = db.session.query(CalendarEventCategory).get(category_id)

    event = CalendarEvent(eventCreatorID=current_user.id,
                  eventTitle=category.fixedTitle, eventDescription='',
                  eventCategoryID=category.categoryID, eventApproved=True,
                  eventTime=event_time)

    accs: Sequence[Account] = db.session.query(Account).filter(or_(Account.id == acc_id for acc_id in backseat_ids)).all()
    for acc in accs:
        event.backseats.append(acc)

    db.session.add(event)





