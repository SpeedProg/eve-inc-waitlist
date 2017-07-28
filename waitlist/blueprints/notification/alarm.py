from flask import render_template
from flask_login import login_required

from . import bp


@bp.route("/alarm")
@login_required
def alarm_idx():
    return render_template("notifications/alarm.html")
