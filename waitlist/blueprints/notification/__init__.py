from flask import Blueprint

bp = Blueprint('notification', __name__)
from .alarm import *