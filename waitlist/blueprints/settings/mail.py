import logging
from flask.blueprints import Blueprint
from flask_login import login_required

from waitlist.blueprints.settings import add_menu_entry
from flask.templating import render_template

from waitlist.permissions import perm_manager
from waitlist.utility.settings import sget_resident_mail,\
    sget_tbadge_mail, sset_tbadge_mail, sset_resident_mail, sset_resident_topic,\
    sset_tbadge_topic, sset_other_mail, sset_other_topic, sget_tbadge_topic,\
    sget_other_mail, sget_resident_topic, sget_other_topic
from flask.globals import request
from flask.helpers import flash, url_for
from werkzeug.utils import redirect
from waitlist.base import app
from flask_babel import gettext, lazy_gettext

bp = Blueprint('settings_mail', __name__)
logger = logging.getLogger(__name__)


perm_manager.define_permission('welcome_mail_edit')
perm_edit = perm_manager.get_permission('welcome_mail_edit')


@app.context_processor
def inject_data():
    return dict()


@bp.route("/")
@login_required
@perm_edit.require()
def index():
    mails = {
         'resident': [sget_resident_mail(), sget_resident_topic()],
         'tbadge': [sget_tbadge_mail(), sget_tbadge_topic()],
         'other': [sget_other_mail(), sget_other_topic()]
         }
    return render_template("settings/mail/index.html", mails=mails)


@bp.route("/change/<string:type_>", methods=["POST"])
@login_required
@perm_edit.require()
def change(type_):
    if type_ == "tbadge":
        mail = request.form.get('mail')
        topic = request.form.get('topic')
        sset_tbadge_mail(mail)
        sset_tbadge_topic(topic)
        flash(gettext("T-Badge mail set!"), 'success')
    elif type_ == "resident":
        mail = request.form.get('mail')
        topic = request.form.get('topic')
        sset_resident_mail(mail)
        sset_resident_topic(topic)
        flash(gettext("Resident mail set!"), 'success')
    elif type_ == "default":
        mail = request.form.get('mail')
        topic = request.form.get('topic')
        sset_other_mail(mail)
        sset_other_topic(topic)
        flash(gettext("Other mail set!"), 'success')
    return redirect(url_for('settings_mail.index'))


add_menu_entry('settings_mail.index', lazy_gettext('IG Mail Settings'), lambda: perm_edit.can())
