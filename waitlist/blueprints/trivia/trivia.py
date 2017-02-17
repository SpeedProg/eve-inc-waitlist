import logging

import flask
from flask import Blueprint
from flask import render_template
from flask import request
from flask.ext.login import current_user
from flask.ext.login import login_required

from waitlist import db
from waitlist.storage.database import TriviaSubmission, Trivia, TriviaSubmissionAnswer

bp = Blueprint('trivia', __name__)
logger = logging.getLogger(__name__)


@bp.route('/', methods=['GET'])
@login_required
def show_input_form():
    return render_template('trivia/index.html')


QUESTION_PREFIX = 'qinput-'


@bp.route('/', methods=['POST'])
@login_required
def process_submission():
    # we are going to hard restrict submissions to
    # one per account and character
    trivia_id = int(request.form['trivia-id'])
    trivia = db.session.query(Trivia).get(trivia_id)

    # lets see if we find a submisson by this character or account
    filter_criteria = None
    if current_user.type == 'account':
        filter_criteria = ((TriviaSubmission.submittorAccountID == current_user.id) | (TriviaSubmission.submittorID == current_user.get_eve_id()))
    else:
        filter_criteria = (TriviaSubmission.submittorID == current_user.get_eve_id())

    filter_criteria &= (TriviaSubmission.triviaID == trivia_id)

    existing_submission = db.session.query(TriviaSubmission).filter(filter_criteria).all()

    if existing_submission is not None:
        flask.abort(409, 'You already submitted answers for this trivia.')

    submission = TriviaSubmission(triviaID=trivia_id)
    submission.submittorID = current_user.get_eve_id()

    if current_user.type == 'account':
        submission.submittorAccountID == current_user.id

    for name in request.form:
        if name.startswith(QUESTION_PREFIX):
            try:
                add_answer_to_database(submission, get_question_id_from_name(name), request.form[name])
            except ValueError:
                logger.exception('Add Answer for a question to database')
                flask.abort(400, 'Invalid Request sent')

    db.session.add(submission)
    db.session.commit()


def get_question_id_from_name(name):
    if not name.startswith(QUESTION_PREFIX):
        raise ValueError('Question ID didn\'t start with the correct prefix.')
    return int(name.replace(QUESTION_PREFIX, 1))


def add_answer_to_database(submission, question_id, answer):
    db_answer = TriviaSubmissionAnswer(questionID=question_id, answerText=answer)
    submission.answers.append(db_answer)

