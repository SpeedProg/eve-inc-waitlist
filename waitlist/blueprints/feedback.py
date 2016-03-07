from flask.blueprints import Blueprint
import logging
from flask_login import login_required, current_user
from flask.templating import render_template
from flask.globals import request
from flask.helpers import flash
from waitlist.storage.database import Feedback
from waitlist import db
import flask
from waitlist.data.perm import perm_officer, perm_feedback

logger = logging.getLogger(__name__)

feedback = Blueprint('feedback', __name__)

@feedback.route("/", methods=["GET"])
@login_required
def index():
    # get old feedback and input data back
    char_id = current_user.get_eve_id()
    feedback = db.session.query(Feedback).filter(Feedback.user == char_id).first()
    return render_template("feedback/index.html", feedback=feedback)

@feedback.route("/", methods=["POST"])
@login_required
def submit():
    likes = request.form['likes']
    if likes == None:
        return flask.abort(400)    
    comment = request.form['comment']
    if comment == None:
        return flask.abort(400)
    
    does_like = False
    if likes == "likes":
        does_like = True
    elif likes == "dislikes":
        does_like = False
    else:
        flask.abort(400)
    
    char_id = current_user.get_eve_id()
    feedback = db.session.query(Feedback).filter(Feedback.user == char_id).first()
    if feedback == None:
        feedback = Feedback()
        feedback.user = char_id
        feedback.likes = does_like
        feedback.comment = comment
        db.session.add(feedback) 
    else:
        feedback.comment = comment
        feedback.likes = does_like
    
    db.session.commit()
    
    flash(u"Thank You for your feedback!", "info")
    
    char_id = current_user.get_eve_id()
    feedback = db.session.query(Feedback).filter(Feedback.user == char_id).first()
    return render_template("feedback/index.html", feedback=feedback)
    
@feedback.route("/settings")
@perm_feedback.require(http_exception=401)
def settings():
    feedbacks = db.session.query(Feedback).order_by(Feedback.last_changed).all()
    yeses = db.session.query(Feedback).filter(Feedback.likes == True).count()
    nos = db.session.query(Feedback).filter(Feedback.likes == False).count()
    return render_template("feedback/settings.html", feedbacks=feedbacks, yeses=yeses, nos=nos)