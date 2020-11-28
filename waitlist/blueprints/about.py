from flask.templating import render_template
from flask.blueprints import Blueprint

bp = Blueprint('about', __name__)

@bp.route("/about", methods=["GET"])
def about():
    return render_template("about.html")
