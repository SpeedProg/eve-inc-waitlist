from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from flask.templating import render_template
from flask.globals import request
from flask.helpers import flash, url_for, make_response
from waitlist.storage.database import Feedback, Ticket
from waitlist.base import db
import flask
from waitlist.data.perm import perm_feedback
from datetime import datetime, timedelta
from sqlalchemy.sql.expression import desc

logger = logging.getLogger(__name__)

feedback = Blueprint('feedback', __name__)

@feedback.route("/", methods=["GET"])
@login_required
def index():
    # get old feedback and input data back
    char_id = current_user.get_eve_id()
    tickets = db.session.query(Ticket).filter(Ticket.characterID == char_id).all()
    return render_template("feedback/index.html", tickets=tickets)

@feedback.route("/", methods=["POST"])
@login_required
def submit():
    title = request.form['title']
    if title == None or len(title) > 50:
        return flask.abort(400, "Title is to long (max 50)")
    message = request.form['message']
    if message == None:
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
    
    flash(u"Thank You for your feedback!", "info")

    return flask.redirect(url_for('.index'))
    
@feedback.route("/settings", methods=["GET"])
@perm_feedback.require(http_exception=401)
def settings():
    # only give tickets that are not "closed" and not older then 90 days
    time90daysAgo = datetime.utcnow() - timedelta(90)
    tickets = db.session.query(Ticket).filter((Ticket.time > time90daysAgo) & (Ticket.state == "new")).order_by(desc(Ticket.time)).all()
    return render_template("feedback/settings.html", tickets=tickets)

@feedback.route("/settings", methods=["POST"])
@perm_feedback.require(http_exception=401)
def change_status():
    ticketID = int(request.form.get('ticketID'))
    newStatus = request.form.get('ticketStatus')
    ticket = db.session.query(Ticket).get(ticketID)
    ticket.state = newStatus
    db.session.commit()
    return make_response(200, "OK")
