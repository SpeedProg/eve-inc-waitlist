from flask.templating import render_template
from flask.blueprints import Blueprint

bp = Blueprint('help', __name__)

@bp.route("/help", methods=["GET"])
def site_help():
    return render_template("help.html")