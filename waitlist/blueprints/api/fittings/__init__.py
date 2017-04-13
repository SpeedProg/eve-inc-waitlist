from flask import Blueprint

bp = Blueprint('api_fittings', __name__)

from .fittings import *
from .comp import *
from .self import *
