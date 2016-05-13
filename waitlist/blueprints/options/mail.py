import logging
from flask.blueprints import Blueprint
from flask_login import login_required
from waitlist.data.perm import perm_access_mod_mail, perm_mod_mail_resident,\
    perm_mod_mail_tbadge
from flask.templating import render_template
from waitlist.utility.settings.settings import sget_resident_mail,\
    sget_tbadge_mail, sset_tbadge_mail, sset_resident_mail
from flask.globals import request
from flask.helpers import flash, url_for
from werkzeug.utils import redirect
from waitlist.base import app

bp = Blueprint('settings_mail', __name__)
logger = logging.getLogger(__name__)

@app.context_processor
def inject_data():
    return dict()

@bp.route("/")
@login_required
@perm_access_mod_mail.require()
def index():
    res_mail = None
    t_mail = None
    if perm_mod_mail_resident.can():
        res_mail = sget_resident_mail()
    if perm_mod_mail_tbadge.can():
        t_mail = sget_tbadge_mail()
    return render_template("/settings/mail/index.html", res_mail=res_mail, t_mail=t_mail)

@bp.route("/change/<string:type_>", methods=["POST"])
@login_required
@perm_access_mod_mail.require()
def change(type_):
    if type_ == "tbadge" and perm_mod_mail_tbadge.can():
        mail = request.form.get('mail')
        sset_tbadge_mail(mail)
        flash("T-Badge mail set!")
    elif type_ == "resident" and perm_mod_mail_resident.can():
        mail = request.form.get('mail')
        sset_resident_mail(mail)
        flash("Resident mail set!")
    return redirect(url_for('settings_mail.index'))