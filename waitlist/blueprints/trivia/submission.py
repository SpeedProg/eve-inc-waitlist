import logging
from datetime import datetime
from typing import Optional

import flask
from flask import Blueprint
from flask import Response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user, login_required

from waitlist import db
from waitlist.storage.database import TriviaSubmission, Trivia, TriviaSubmissionAnswer


logger = logging.getLogger(__name__)
bp = Blueprint('trivia_submission', __name__)


@bp.route('/<int:trivia_id>', methods=['GET'])
@login_required
def show_input_form(trivia_id: int):
    trivia = db.session.query(Trivia).get(trivia_id)
    if trivia is None:
        flask.abort(404, 'This trivia does not exist')
    timenow = datetime.utcnow()
    if trivia.toTime < timenow:
        flask.abort(410, f'This trivia is over, it ended at {trivia.toTime} and it is {timenow}')
    if trivia.fromTime > timenow:
        flask.abort(428, f'This trivia did not start yet, it starts at {trivia.fromTime} and it is {timenow}')

    return render_template('trivia/index.html', trivia=trivia)


QUESTION_PREFIX = 'qinput-'


@bp.route('/<int:trivia_id>', methods=['POST'])
@login_required
def process_submission(trivia_id: int) -> Optional[Response]:
    # we are going to hard restrict submissions to
    # one per account and character
    trivia = db.session.query(Trivia).get(trivia_id)
    if trivia is None:
        flask.abort(404, 'This trivia does not exist')
    timenow = datetime.utcnow()
    if trivia.toTime < timenow:
        flask.abort(410, f'This trivia is over, it ended at {trivia.toTime} and it is {timenow}')
    if trivia.fromTime > timenow:
        flask.abort(428, f'This trivia did not start yet, it starts at {trivia.fromTime} and it is {timenow}')

    # lets see if we find a submisson by this character or account
    if current_user.type == "account":
        filter_criteria = ((TriviaSubmission.submittorAccountID == current_user.id)
                           | (TriviaSubmission.submittorID == current_user.get_eve_id()))
    else:
        filter_criteria = (TriviaSubmission.submittorID == current_user.get_eve_id())

    filter_criteria &= (TriviaSubmission.triviaID == trivia_id)

    existing_submission = db.session.query(TriviaSubmission).filter(filter_criteria).first()

    if existing_submission is not None:
        flask.abort(409, 'You already submitted answers for this trivia.')

    submission = TriviaSubmission(triviaID=trivia_id)
    submission.submittorID = current_user.get_eve_id()

    if current_user.type == "account":
        submission.submittorAccountID = current_user.id

    for name in request.form:
        if name.startswith(QUESTION_PREFIX):
            try:
                add_answer_to_database(submission, get_question_id_from_name(name), request.form[name])
            except ValueError:
                logger.exception('Add Answer for a question to database')
                flask.abort(400, 'Invalid Request sent')

    db.session.add(submission)
    db.session.commit()
    flask.flash('Thank you for participating, winners will be announced after the trivia is finished', 'info')
    return redirect(url_for('index'))


def get_question_id_from_name(name):
    if not name.startswith(QUESTION_PREFIX):
        raise ValueError('Question ID didn\'t start with the correct prefix.')
    return int(name.replace(QUESTION_PREFIX, '', 1))


def add_answer_to_database(submission, question_id, answer):
    db_answer = TriviaSubmissionAnswer(questionID=question_id, answerText=answer)
    submission.answers.append(db_answer)
