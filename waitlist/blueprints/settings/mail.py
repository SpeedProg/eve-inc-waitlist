import logging
from flask.blueprints import Blueprint
from flask_login import login_required
from waitlist.data.perm import perm_access_mod_mail, perm_mod_mail_resident,\
    perm_mod_mail_tbadge, perm_leadership
from flask.templating import render_template
from waitlist.utility.settings import sget_resident_mail,\
    sget_tbadge_mail, sset_tbadge_mail, sset_resident_mail, sset_resident_topic,\
    sset_tbadge_topic, sset_other_mail, sset_other_topic, sget_tbadge_topic,\
    sget_other_mail, sget_resident_topic, sget_other_topic
from flask.globals import request
from flask.helpers import flash, url_for
from werkzeug.utils import redirect
from waitlist import app

bp = Blueprint('settings_mail', __name__)
logger = logging.getLogger(__name__)


@app.context_processor
def inject_data():
    return dict()


@bp.route("/")
@login_required
@perm_access_mod_mail.require()
def index():
    mails = {
         'resident': [sget_resident_mail(), sget_resident_topic()],
         'tbadge': [sget_tbadge_mail(), sget_tbadge_topic()],
         'other': [sget_other_mail(), sget_other_topic()]
         }
    return render_template("settings/mail/index.html", mails=mails)


@bp.route("/change/<string:type_>", methods=["POST"])
@login_required
@perm_access_mod_mail.require()
def change(type_):
    if type_ == "tbadge" and perm_mod_mail_tbadge.can():
        mail = request.form.get('mail')
        topic = request.form.get('topic')
        sset_tbadge_mail(mail)
        sset_tbadge_topic(topic)
        flash("T-Badge mail set!")
    elif type_ == "resident" and perm_mod_mail_resident.can():
        mail = request.form.get('mail')
        topic = request.form.get('topic')
        sset_resident_mail(mail)
        sset_resident_topic(topic)
        flash("Resident mail set!")
    elif type_ == "default" and perm_leadership.can():
        mail = request.form.get('mail')
        topic = request.form.get('topic')
        sset_other_mail(mail)
        sset_other_topic(topic)
        flash("Other mail set!")
    return redirect(url_for('settings_mail.index'))
