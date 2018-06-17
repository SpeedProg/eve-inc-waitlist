from waitlist.blueprints.swagger_api.statistics.blueprint import bp_v1
from flask_login.utils import login_required
from waitlist.permissions import perm_manager
from flask.wrappers import Response
from waitlist.blueprints.swagger_api.statistics.data import StatsManager
from datetime import timedelta
from flask import jsonify


perm_access = perm_manager.get_permission('settings_access')


@login_required
@perm_access.require()
@bp_v1.route('/distinct_hull_character/<int:duration_seconds>',
             methods=['GET'])
def distinct_hull_character_get_v1(duration_seconds: int) -> Response:
    """
    file: distinct_hull_character_get_v1.yml
    """
    statistic_data = StatsManager.get_distinct_hull_character_stats(
        timedelta(seconds=duration_seconds)
    )

    return jsonify(statistic_data)


@login_required
@perm_access.require()
@bp_v1.route('/approved_fits_by_account/<int:duration_seconds>',
             methods=['GET'])
def approved_fits_by_account_v1(duration_seconds: int) -> Response:
    """
    file: approved_fits_by_account_get_v1.yml
    """
    statistic_data = StatsManager.get_approved_fits_by_account_stats(
        timedelta(seconds=duration_seconds)
    )

    return jsonify(statistic_data)

@login_required
@perm_access.require()
@bp_v1.route('/joined_members/<int:duration_seconds>',
             methods=['GET'])
def joined_members_v1(duration_seconds: int) -> Response:
    """
    file: joined_members_get_v1.yml
    """
    statistic_data = StatsManager.get_joined_members_stats(
        timedelta(seconds=duration_seconds)
    )

    return jsonify(statistic_data)