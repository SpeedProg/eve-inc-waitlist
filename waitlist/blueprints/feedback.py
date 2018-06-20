from flask import Response
from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from flask.templating import render_template
from flask.globals import request
from flask.helpers import flash, url_for, make_response

from waitlist.blueprints.settings import add_menu_entry
from waitlist.permissions import perm_manager
from waitlist.storage.database import Ticket
from waitlist import db
import flask
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import desc
from flask_babel import gettext, lazy_gettext

logger = logging.getLogger(__name__)

feedback = Blueprint('feedback', __name__)


perm_manager.define_permission('feedback_view')
perm_manager.define_permission('feedback_edit')

perm_view = perm_manager.get_permission('feedback_view')
perm_edit = perm_manager.get_permission('feedback_edit')


@feedback.route("/", methods=["GET"])
@login_required
def index() -> Response:
    # get old feedback and input data back
    char_id = current_user.get_eve_id()
    tickets = db.session.query(Ticket).filter(Ticket.characterID == char_id).all()
    return render_template("feedback/index.html", tickets=tickets)


@feedback.route("/", methods=["POST"])
@login_required
def submit() -> Response:
    title = request.form['title']
    if title is None or len(title) > 50:
        return flask.abort(400, "Title is to long (max 50)")
    message = request.form['message']
    if message is None:
        return flask.abort(400)
    
    char_id = current_user.get_eve_id()
    if message != "":
        ticket = Ticket(
                        title=title,
                        characterID=char_id,
                        message=message,
                        state="new"
                        )
        db.session.add(ticket)
    
    db.session.commit()
    
    flash(gettext("Thank You for your feedback!"), "info")

    return flask.redirect(url_for('.index'))


@feedback.route("/settings", methods=["GET"])
@perm_view.require(http_exception=401)
def settings() -> Response:
    # only give tickets that are not "closed" and not older then 90 days
    time_90days_ago = datetime.utcnow() - timedelta(90)
    tickets = db.session.query(Ticket).filter((Ticket.time > time_90days_ago) & (Ticket.state == "new"))\
        .order_by(desc(Ticket.time)).all()
    return render_template("feedback/settings.html", tickets=tickets)


@feedback.route("/settings", methods=["POST"])
@perm_edit.require(http_exception=401)
def change_status() -> Response:
    ticket_id = int(request.form.get('ticketID'))
    new_status = request.form.get('ticketStatus')
    ticket = db.session.query(Ticket).get(ticket_id)
    ticket.state = new_status
    db.session.commit()
    return make_response("OK")


add_menu_entry('feedback.settings', lazy_gettext('Feedback'), perm_view.can)
