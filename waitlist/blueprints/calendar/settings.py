import logging
import string
from datetime import datetime
from typing import List, Sequence, Optional

from flask import Blueprint
from flask import make_response
from flask import redirect
from flask import render_template
from flask import url_for
from flask.globals import request
from flask_login import login_required, current_user
from sqlalchemy import or_

from waitlist import db
from waitlist.permissions import perm_manager
from waitlist.storage.database import Account, CalendarEvent, CalendarEventCategory
import flask

bp = Blueprint('calendar_settings', __name__)
logger = logging.getLogger(__name__)

perm_manager.define_permission('calendar_event_see_all')
perm_manager.define_permission('calendar_event_delete_other')


@bp.route("/", methods=['GET'])
@login_required
@perm_manager.require('commandcore')
def get_index():
    # noinspection PyPep8
    accounts: Sequence[Account] = db.session.query(Account).filter(Account.disabled == False).all()

    event_query = db.session.query(CalendarEvent).filter(CalendarEvent.eventTime > datetime.utcnow())
    if not perm_manager.get_permission('calendar_event_see_all').can():
        event_query = event_query \
            .filter((CalendarEvent.eventCreatorID == current_user.id)
                    | (CalendarEvent.backseats.any(Account.id == current_user.id))
                    | (CalendarEvent.organizers.any(Account.id == current_user.id)))

    event_query.order_by(CalendarEvent.eventTime.asc())
    events = event_query.all()

    categories = db.session.query(CalendarEventCategory).all()

    return render_template('calendar/settings.html', accounts=accounts, events=events, categories=categories)


@bp.route("/", methods=['POST'])
@login_required
@perm_manager.require('commandcore')
def post_index():
    for name in ['categoryID', 'time', 'date']:
        if name not in request.form:
            flask.abort(400, 'Some required information is missing')

    category_id: int = int(request.form['categoryID'])
    backseats_string: List[string] = request.form.getlist('backseats')
    event_time: str = request.form['time']
    event_date: str = request.form['date']

    if event_time == '' or event_date == '':
        flask.abort(400, 'Event time or date was not specified')

    backseat_ids: List[int] = []
    print(backseats_string)
    for backseat_string in backseats_string:
        backseat_ids.append(int(backseat_string))

    event_datetime: datetime = datetime.strptime(event_date+' '+event_time, "%Y-%m-%d %H:%M")

    category: CalendarEventCategory = db.session.query(CalendarEventCategory).get(category_id)

    desc: Optional[str] = category.fixedDescription
    if desc is None:
        desc = ''

    event = CalendarEvent(eventCreatorID=current_user.id,
                          eventTitle=category.fixedTitle, eventDescription=desc,
                          eventCategoryID=category.categoryID, eventApproved=True,
                          eventTime=event_datetime)

    accs: Sequence[Account] = db.session.query(Account).filter(
        Account.id.in_(backseat_ids)
        ).all()
    for acc in accs:
        event.backseats.append(acc)

    db.session.add(event)
    db.session.commit()
    return redirect(url_for('.get_index'))


@bp.route("/event/<int:event_id>", methods=['DELETE'])
@login_required
@perm_manager.require('commandcore')
def delete_event_id(event_id):
    # if they are council they can delete everything
    event = db.session.query(CalendarEvent).get(event_id)
    if perm_manager.get_permission('calendar_event_delete_other').can():
        logger.info("%s with id %d is deleting event Title[%s] by Account[%s, %d]", current_user.username,
                    current_user.id, event.eventTitle, event.creator.username, event.creator.id)
        db.session.delete(event)
        db.session.commit()
        return make_response("Event with id[" + str(event_id) + "] deleted", 200)

    elif event.creator.id == current_user.id:
        logger.info("%s with id %d is deleting how own event Title[%s]", current_user.username, current_user.id,
                    event.eventTitle)
        db.session.delete(event)
        db.session.commit()
        return make_response("You successfully deleted your own event", 200)
    else:
        logger.error("%s tried to delete event %d not owned by him", current_user.username, event.eventID)
        return make_response(
            "You are not allowed to delete other peoples events, and this does not seem to be your event!", 403)
