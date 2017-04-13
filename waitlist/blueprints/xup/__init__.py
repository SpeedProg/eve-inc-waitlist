from flask import Blueprint

bp = Blueprint('xup', __name__)
from .submission import *
